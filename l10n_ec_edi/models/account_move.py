# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.l10n_ec_edi.models.access_key import AccessKey
import base64

# SRI 2026 Regulatory Constants
CF_RUC = '9999999999999'
CF_LIMIT_USD = 50.00
MAX_ANNULMENT_DAYS = 7


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_ec_sri_access_key = fields.Char(string="SRI Access Key", copy=False, help="49-digit Clave de Acceso")
    l10n_ec_sri_status = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
        ('sent', 'Sent'),
        ('authorized', 'Authorized'),
        ('rejected', 'Rejected'),
    ], string="SRI Status", default='draft', copy=False, index=True)
    l10n_ec_xml_data = fields.Binary("Signed XML", attachment=True, copy=False)
    l10n_ec_sri_response = fields.Text("SRI Response", copy=False)

    # Purchses Extensions (ATS)
    l10n_ec_sustento_code = fields.Selection([
        ('01', '01 - Crédito Tributario para IVA'),
        ('02', '02 - Costo o Gasto'),
        ('03', '03 - Activo Fijo'),
        ('04', '04 - Liquidación Gastos'),
        ('05', '05 - Liquidación Reembolsos'),
        ('06', '06 - Sin Crédito Tributario'),
        ('07', '07 - Pagos Reembolsos'),
    ], string="Sustento Tributario", help="SRI code explaining the purchase purpose (ATS)")

    # =========================================================================
    # SRI 2026 REGULATORY VALIDATIONS
    # =========================================================================

    @api.constrains('amount_total', 'partner_id', 'move_type')
    def _check_consumidor_final_limit(self):
        """
        SRI 2026 Rule: Consumidor Final invoices cannot exceed $50 USD.
        Resolution NAC-DGERCGC25-00000017
        """
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue
            if move.partner_id and move.partner_id.vat == CF_RUC:
                if move.amount_total > CF_LIMIT_USD:
                    raise ValidationError(_(
                        "SRI 2026 Regulation: Invoices to Consumidor Final (9999999999999) "
                        "cannot exceed $%.2f USD. Current total: $%.2f"
                    ) % (CF_LIMIT_USD, move.amount_total))

    @api.constrains('state')
    def _check_annulment_deadline(self):
        """
        SRI 2026 Rule: Authorized invoices can only be annulled until
        day 7 of the month following emission.
        Resolution NAC-DGERCGC25-00000017
        """
        from datetime import date
        for move in self:
            if move.state == 'cancel' and move.l10n_ec_sri_status == 'authorized':
                if move.invoice_date:
                    emission_date = move.invoice_date
                    today = date.today()

                    # Calculate deadline: day 7 of next month
                    if emission_date.month == 12:
                        deadline = date(emission_date.year + 1, 1, 7)
                    else:
                        deadline = date(emission_date.year, emission_date.month + 1, 7)

                    if today > deadline:
                        raise ValidationError(_(
                            "SRI 2026 (Res. NAC-DGERCGC25-00000017): "
                            "No se puede anular esta factura autorizada.\n\n"
                            "Fecha de emisión: %s\n"
                            "Fecha límite de anulación: %s\n"
                            "Fecha actual: %s"
                        ) % (emission_date, deadline, today))

    # 2026 Mandate: No cancellation of Consumidor Final
    def button_cancel_sri(self):
        for move in self:
            if move.l10n_ec_sri_status == 'authorized':
                # Check for Consumidor Final Rule
                if move.partner_id.vat == '9999999999999':
                     raise UserError(_("SRI 2026 Rule: Cannot cancel Authorized invoices for Consumidor Final."))
        return super(AccountMove, self).button_cancel() # Standard cancel logic needs review

    def _generate_access_key(self):
        for move in self:
            # Only for Ecuador
            if move.company_id.country_id.code != 'EC':
                continue

            # Use AccessKey helper
            company = move.company_id
             # Environment: 1=Test, 2=Prod
            env = '2' if company.l10n_ec_sri_environment == 'production' else '1'
            # Get establishment/emission point from company or default
            estab = getattr(company, 'l10n_ec_establishment', '001') or '001'
            pto = getattr(company, 'l10n_ec_emission_point', '001') or '001'
            seq = move.name.split('/')[-1] if '/' in move.name else move.name[-9:] # Simple logic, needs refinement

            key = AccessKey.generate(
                invoice_date=move.invoice_date,
                doc_type=move.l10n_latam_document_type_id.code,
                ruc=company.vat,
                environment=env,
                establishment=estab,
                emission_point=pto,
                sequential=seq
            )
            move.l10n_ec_sri_access_key = key

    def action_send_sri(self):
        """
        Trigger Manual Send to SRI.
        """
        for move in self:
            if move.state != 'posted':
                raise UserError(_("Invoice must be Posted before sending to SRI."))

            # 1. Certificate Check
            certificate = move.company_id.l10n_ec_certificate_id
            if not certificate or certificate.state != 'active':
                raise UserError(_("SRI Error: No active Signing Certificate configured for company %s") % move.company_id.name)

            # 2. Generate Access Key
            if not move.l10n_ec_sri_access_key:
                move._generate_access_key()

            # 3. Generate XML
            # Use the method injected into account.edi.format by our l10n_ec_edi module
            try:
                # We interpret 'account.edi.format' as the model where the method exists.
                # Since it's an override, we can call it on an empty recordset or any record.
                xml_content = self.env['account.edi.format']._export_l10n_ec_edi(move)
            except AttributeError:
                # Fallback if method lookup fails (e.g. if _name was different)
                raise UserError(_("EDI Format method _export_l10n_ec_edi not found. Check installation."))

            # 4. Sign XML
            signer = self.env['l10n_ec.sri.signer']
            try:
                signed_xml_bytes = signer.sign_xml(
                    xml_content.encode('utf-8'),
                    certificate.content,
                    certificate.password
                )
            except Exception as e:
                raise UserError(_("Signing Error: %s") % str(e))

            # 5. Send to SRI
            service = self.env['l10n_ec.sri.service']
            env_code = '2' if move.company_id.l10n_ec_sri_environment == 'production' else '1'

            response = service.send_document(signed_xml_bytes, env_code)

            # 6. Process Response
            if response.get('status') == 'RECIBIDA':
                move.l10n_ec_sri_status = 'sent'
                move.l10n_ec_sri_response = "RECIBIDA. Waiting for Authorization..."

                # Store XML
                move.l10n_ec_xml_data = base64.b64encode(signed_xml_bytes)
            else:
                move.l10n_ec_sri_status = 'rejected'
                msgs = "\n".join(response.get('messages', []))
                move.l10n_ec_sri_response = f"{response.get('status')}: {msgs}"
                # We do not block the UI with error unless critical?
                # Better to raise UserError so user knows it failed immediately?
                # Yes, for manual button, raise error if rejected.
                raise UserError(_("SRI Rejected: %s") % msgs)
