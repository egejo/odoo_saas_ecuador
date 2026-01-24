# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import base64

class AccountRetention(models.Model):
    _name = 'account.retention'
    _description = 'Comprobante de Retención (Ecuador)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'

    name = fields.Char(string='Document Number', required=True, copy=False, readonly=True, index=True, default='Draft')
    company_id = fields.Many2one('res.company', index=True, required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, index=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)

    # SRI Integration Fields (Direct Link to Shared Logic)
    l10n_ec_sri_access_key = fields.Char(string="SRI Access Key", copy=False)
    l10n_ec_sri_status = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
        ('sent', 'Sent'),
        ('authorized', 'Authorized'),
        ('rejected', 'Rejected'),
    ], string="SRI Status", default='draft', copy=False, index=True, tracking=True)
    l10n_ec_sri_response = fields.Text("SRI Response")
    l10n_ec_xml_data = fields.Binary("XML File", attachment=True)

    # Lines
    retention_line_ids = fields.One2many('account.retention.line', 'retention_id', string='Withholding Lines')

    invoice_id = fields.Many2one('account.move', string='Related Bill', domain=[('move_type', '=', 'in_invoice')])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    @api.constrains('date', 'invoice_id')
    def _check_5_day_rule(self):
        """
        Enforce Rule VAL-R02: Retention must be issued within 5 days of invoice date.
        """
        for record in self:
            if record.invoice_id and record.date:
                inv_date = record.invoice_id.invoice_date
                if not inv_date:
                    continue
                # 5 Days tolerance
                delta = (record.date - inv_date).days
                if delta > 5:
                    raise ValidationError(_(
                        "SRI Regulation Check Failed (VAL-R02): "
                        "Retention date %s is %s days after Invoice date %s. "
                        "Maximum allowed is 5 days."
                    ) % (record.date, delta, inv_date))
                if delta < 0:
                    raise ValidationError(_("Retention date cannot be before Invoice date."))

    @api.model
    def create(self, vals):
        if vals.get('name', 'Draft') == 'Draft':
             vals['name'] = self.env['ir.sequence'].next_by_code('account.retention') or 'Draft'
        return super(AccountRetention, self).create(vals)

    def action_post(self):
        self.write({'state': 'posted'})
        # Trigger SRI flow here in future

    def _generate_access_key(self):
        """
        Uses l10n_ec_edi.models.access_key
        """
        for record in self:
            if not record.l10n_ec_sri_access_key:
                from ..models.access_key import AccessKey # Import from EDI module?
                # Better: Use the shared helper if possible or re-implement simple call
                # Since l10n_ec_edi is a dependency, we can import from it.
                # However, Odoo imports are tricky.
                # Let's rely on the method being available or duplicate the helper call for safety in this scope?
                # No, duplicating code is bad.
                # We can call the helper class from l10n_ec_edi.models.access_key
                # But it's not an Odoo model.

                # Option B: Add a transient model or utility in EDI to generate keys.
                # Or just import it:
                from odoo.addons.l10n_ec_edi.models.access_key import AccessKey

                # Check environment
                env = '2' if record.company_id.l10n_ec_sri_environment == 'production' else '1'

                # Parse sequence "001-001-000000001"
                parts = record.name.split('-')
                if len(parts) == 3:
                    estab, pto, seq = parts
                else:
                    # Fallback for draft/bad format
                    estab, pto = '001', '001'
                    seq = record.id

                key = AccessKey.generate(
                    invoice_date=record.date,
                    doc_type='07', # Retention
                    ruc=record.company_id.vat,
                    environment=env,
                    establishment=estab,
                    emission_point=pto,
                    sequential=seq
                )
                record.l10n_ec_sri_access_key = key

    def action_send_sri(self):
        """
        Generates XML, Signs it, and Sends to SRI.
        """
        for record in self:
            if not record.l10n_ec_sri_access_key:
                record._generate_access_key()

            # 1. Render XML
            values = {
                'retention': record,
                'company': record.company_id,
                'partner': record.partner_id,
                'environment': '1' if record.company_id.l10n_ec_sri_environment == 'test' else '2',
                'access_key': record.l10n_ec_sri_access_key,
                'format_monetary': lambda x: "%.2f" % x,
                'format_float': lambda x, p: ("%." + str(p) + "f") % x,
                'identifier_code': '05' if record.partner_id.l10n_ec_identifier_type == 'cedula' else '04' # Simplified
            }
            xml_content = self.env['ir.qweb']._render('l10n_ec_withholding.l10n_ec_retention_xml', values)

            # 2. Sign
            certificate = record.company_id.l10n_ec_certificate_id
            if not certificate or certificate.state != 'active':
                 raise UserError(_("SRI Error: No active Signing Certificate configured."))

            try:
                # Use AbstractModels from l10n_ec_edi
                signer = self.env['l10n_ec.sri.signer']
                service = self.env['l10n_ec.sri.service']

                signed_xml_bytes = signer.sign_xml(
                    xml_content.encode('utf-8'),
                    certificate.content,
                    certificate.password
                )

                # 3. Transmit
                env_code = '1' if record.company_id.l10n_ec_sri_environment == 'test' else '2'
                response_data = service.send_document(signed_xml_bytes, env_code)

                # 4. Process
                if response_data.get('status') == 'RECIBIDA':
                     record.l10n_ec_sri_status = 'sent'
                     record.l10n_ec_sri_response = "RECIBIDA. Waiting for Authorization..."
                else:
                     record.l10n_ec_sri_status = 'rejected'
                     msgs = "\n".join(response_data.get('messages', []))
                     record.l10n_ec_sri_response = f"{response_data.get('status')}: {msgs}"

                record.l10n_ec_xml_data = base64.b64encode(signed_xml_bytes)

            except Exception as e:
                record.l10n_ec_sri_response = f"System Error: {str(e)}"
                # Don't rollback, save the error

