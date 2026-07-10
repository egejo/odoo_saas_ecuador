# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.l10n_ec_edi.models.access_key import AccessKey
import base64

# =========================================================================
# SRI 2026 CONFIGURACIÓN
# Todos los valores regulatorios se leen de ir.config_parameter
# para permitir actualizaciones sin modificar código.
# NO HARDCODED DEFAULTS - System must be properly configured.
# =========================================================================


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_ec_sri_access_key = fields.Char(
        string="SRI Access Key", copy=False, help="49-digit Clave de Acceso"
    )
    l10n_ec_sri_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("signed", "Signed"),
            ("sent", "Sent"),
            ("authorized", "Authorized"),
            ("rejected", "Rejected"),
        ],
        string="SRI Status",
        default="draft",
        copy=False,
        index=True,
    )
    l10n_ec_xml_data = fields.Binary("Signed XML", attachment=True, copy=False)
    l10n_ec_sri_response = fields.Text("SRI Response", copy=False)

    # Purchases Extensions (ATS) -- Tabla 5 de la Ficha Tecnica ATS del SRI.
    # Catalogo corregido 2026-07-10: la version anterior (heredada del
    # upstream) tenia las etiquetas 05/06/07 equivocadas (mezclaba
    # "Liquidacion Reembolsos"/"Sin Credito Tributario"/"Pagos Reembolsos",
    # que no son las descripciones reales de esos codigos en la Tabla 5) --
    # mismo patron de codigos SRI mal etiquetados ya visto varias veces en
    # este fork (retenciones, ICE). Se completa ademas con los codigos
    # 00/08-13 que faltaban por completo.
    l10n_ec_sustento_code = fields.Selection(
        [
            (
                "01",
                "01 - Crédito Tributario para declaración de IVA (bienes/servicios)",
            ),
            ("02", "02 - Costo o Gasto para declaración de IR (bienes/servicios)"),
            ("03", "03 - Activo Fijo - Crédito Tributario para IVA"),
            ("04", "04 - Activo Fijo - Costo o Gasto para IR"),
            (
                "05",
                "05 - Liquidación Gastos de Viaje, hospedaje y alimentación (IR)",
            ),
            ("06", "06 - Inventario - Crédito Tributario para IVA"),
            ("07", "07 - Inventario - Costo o Gasto para IR"),
            ("08", "08 - Valor pagado para solicitar Reembolso de Gasto"),
            ("09", "09 - Reembolso por Siniestros"),
            ("10", "10 - Distribución de Dividendos, Beneficios o Utilidades"),
            ("11", "11 - Convenios de débito o recaudación para IFI's"),
            ("12", "12 - Impuestos y retenciones presuntivos"),
            (
                "13",
                "13 - Valores reconocidos por entidades del sector público",
            ),
        ],
        string="Sustento Tributario",
        help="Código SRI (Tabla 5 de la Ficha Técnica ATS) que sustenta la compra.",
    )

    # =========================================================================
    # SRI 2026 REGULATORY VALIDATIONS
    # =========================================================================

    def _get_cf_ruc(self):
        """Retorna el RUC de Consumidor Final desde configuración."""
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_ec.consumidor_final_ruc")
        )
        if not param:
            raise ValidationError(
                _(
                    "Missing configuration: l10n_ec.consumidor_final_ruc\n"
                    "Please install l10n_ec module or configure System Parameters."
                )
            )
        return param

    def _get_cf_limit(self):
        """Retorna el límite de factura CF desde configuración."""
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_ec.consumidor_final_limit")
        )
        if not param:
            raise ValidationError(
                _(
                    "Missing configuration: l10n_ec.consumidor_final_limit\n"
                    "Please install l10n_ec module or configure System Parameters."
                )
            )
        return float(param)

    def _get_annulment_day(self):
        """Retorna el día límite para anulación desde configuración."""
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_ec.annulment_day_limit")
        )
        if not param:
            raise ValidationError(
                _(
                    "Missing configuration: l10n_ec.annulment_day_limit\n"
                    "Please install l10n_ec module or configure System Parameters."
                )
            )
        return int(param)

    @api.constrains("amount_total", "partner_id", "move_type")
    def _check_consumidor_final_limit(self):
        """
        SRI 2026 Rule: Consumidor Final invoices cannot exceed configured limit.
        Resolution NAC-DGERCGC25-00000017
        Default limit: $50 USD (configurable via l10n_ec.consumidor_final_limit)
        """
        for move in self:
            if move.move_type not in ("out_invoice", "out_refund"):
                continue

            cf_ruc = move._get_cf_ruc()
            cf_limit = move._get_cf_limit()

            if move.partner_id and move.partner_id.vat == cf_ruc:
                if move.amount_total > cf_limit:
                    raise ValidationError(
                        _(
                            "Regulación SRI 2026: Facturas a Consumidor Final (%s) "
                            "no pueden superar $%.2f USD.\n"
                            "Total actual: $%.2f"
                        )
                        % (cf_ruc, cf_limit, move.amount_total)
                    )

    @api.constrains("state")
    def _check_annulment_deadline(self):
        """
        SRI 2026 Rule: Authorized invoices can only be annulled until
        day 7 of the month following emission.
        Resolution NAC-DGERCGC25-00000017
        """
        from datetime import date

        for move in self:
            if move.state == "cancel" and move.l10n_ec_sri_status == "authorized":
                if move.invoice_date:
                    emission_date = move.invoice_date
                    today = AccessKey.today_ec()

                    # Calculate deadline: day 7 of next month
                    if emission_date.month == 12:
                        deadline = date(emission_date.year + 1, 1, 7)
                    else:
                        deadline = date(emission_date.year, emission_date.month + 1, 7)

                    if today > deadline:
                        raise ValidationError(
                            _(
                                "SRI 2026 (Res. NAC-DGERCGC25-00000017): "
                                "No se puede anular esta factura autorizada.\n\n"
                                "Fecha de emisión: %s\n"
                                "Fecha límite de anulación: %s\n"
                                "Fecha actual: %s"
                            )
                            % (emission_date, deadline, today)
                        )

    # 2026 Mandate: No cancellation of Consumidor Final
    def button_cancel_sri(self):
        """Cancel invoice with SRI 2026 validations."""
        for move in self:
            if move.l10n_ec_sri_status == "authorized":
                # Check for Consumidor Final Rule - use configurable RUC
                cf_ruc = move._get_cf_ruc()
                if move.partner_id.vat == cf_ruc:
                    raise UserError(
                        _(
                            "SRI 2026: Facturas autorizadas a Consumidor Final (%s) "
                            "no pueden ser anuladas."
                        )
                        % cf_ruc
                    )

                # Check annulment deadline
                move._check_cancellation_allowed()

        return super(AccountMove, self).button_cancel()

    def _check_cancellation_allowed(self):
        """Validate cancellation deadline (day 7 of next month)."""
        from datetime import date

        self.ensure_one()

        if not self.invoice_date:
            return True

        annulment_day = self._get_annulment_day()
        today = AccessKey.today_ec()
        emission = self.invoice_date

        # Calculate deadline
        if emission.month == 12:
            deadline = date(emission.year + 1, 1, annulment_day)
        else:
            deadline = date(emission.year, emission.month + 1, annulment_day)

        if today > deadline:
            raise ValidationError(
                _(
                    "SRI 2026: No se puede anular.\n\n"
                    "Fecha límite: día %s del mes siguiente.\n"
                    "Emisión: %s | Límite: %s | Hoy: %s"
                )
                % (annulment_day, emission, deadline, today)
            )

        return True

    def _generate_access_key(self):
        for move in self:
            # Only for Ecuador
            if move.company_id.country_id.code != "EC":
                continue

            # Use AccessKey helper
            company = move.company_id
            # Environment: 1=Test, 2=Prod
            env = "2" if company.l10n_ec_sri_environment == "production" else "1"
            # Get establishment/emission point from company or default
            estab = getattr(company, "l10n_ec_establishment", "001") or "001"
            pto = getattr(company, "l10n_ec_emission_point", "001") or "001"
            seq = (
                move.name.split("/")[-1] if "/" in move.name else move.name[-9:]
            )  # Simple logic, needs refinement

            key = AccessKey.generate(
                invoice_date=move.invoice_date,
                doc_type=move.l10n_latam_document_type_id.code,
                ruc=company.vat,
                environment=env,
                establishment=estab,
                emission_point=pto,
                sequential=seq,
            )
            move.l10n_ec_sri_access_key = key

    def action_send_sri(self):
        """
        Trigger Manual Send to SRI.
        """
        for move in self:
            if move.state != "posted":
                raise UserError(_("Invoice must be Posted before sending to SRI."))

            # 1. Certificate Check
            certificate = move.company_id.l10n_ec_certificate_id
            if not certificate or certificate.state != "active":
                raise UserError(
                    _(
                        "SRI Error: No active Signing Certificate configured for company %s"
                    )
                    % move.company_id.name
                )

            # 2. Generate Access Key
            if not move.l10n_ec_sri_access_key:
                move._generate_access_key()

            # 3. Generate XML
            # Use the method injected into account.edi.format by our l10n_ec_edi module
            try:
                # We interpret 'account.edi.format' as the model where the method exists.
                # Since it's an override, we can call it on an empty recordset or any record.
                xml_content = self.env["account.edi.format"]._export_l10n_ec_edi(move)
            except AttributeError:
                # Fallback if method lookup fails (e.g. if _name was different)
                raise UserError(
                    _(
                        "EDI Format method _export_l10n_ec_edi not found. Check installation."
                    )
                )

            # 4. Sign XML
            signer = self.env["l10n_ec.sri.signer"]
            try:
                signed_xml_bytes = signer.sign_xml(
                    xml_content.encode("utf-8"),
                    certificate.content,
                    certificate.password,
                )
            except Exception as e:
                raise UserError(_("Signing Error: %s") % str(e))

            # 5. Send to SRI
            service = self.env["l10n_ec.sri.service"]
            env_code = (
                "2" if move.company_id.l10n_ec_sri_environment == "production" else "1"
            )

            response = service.send_document(signed_xml_bytes, env_code)

            # 6. Process Response
            if response.get("status") == "RECIBIDA":
                move.l10n_ec_sri_status = "sent"
                move.l10n_ec_sri_response = "RECIBIDA. Waiting for Authorization..."

                # Store XML
                move.l10n_ec_xml_data = base64.b64encode(signed_xml_bytes)
            else:
                move.l10n_ec_sri_status = "rejected"
                msgs = "\n".join(response.get("messages", []))
                move.l10n_ec_sri_response = f"{response.get('status')}: {msgs}"
                raise UserError(_("SRI Rechazado: %s") % msgs)

    # =========================================================================
    # AUTO-SEND TO SRI ON POST (2026 IMMEDIATE TRANSMISSION REQUIREMENT)
    # =========================================================================

    def action_post(self):
        """
        Override to auto-send to SRI when configured.

        SRI 2026 (Res. NAC-DGERCGC25-00000017):
        Transmisión INMEDIATA de comprobantes electrónicos.
        """
        result = super(AccountMove, self).action_post()

        # Check if auto-send is enabled
        auto_send = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_ec.auto_send_sri", "False")
        )

        if auto_send.lower() in ("true", "1", "yes"):
            for move in self:
                # Only for Ecuador sales invoices
                if move.company_id.country_id.code != "EC":
                    continue
                if move.move_type not in ("out_invoice", "out_refund"):
                    continue

                # Check if certificate is configured
                certificate = move.company_id.l10n_ec_certificate_id
                if not certificate or certificate.state != "active":
                    # No certificate - skip auto-send, log warning
                    import logging

                    _logger = logging.getLogger(__name__)
                    _logger.warning(
                        "SRI Auto-send skipped for %s: No active certificate", move.name
                    )
                    continue

                # Auto-send to SRI
                try:
                    move.action_send_sri()
                except Exception as e:
                    # Log error but don't block posting
                    import logging

                    _logger = logging.getLogger(__name__)
                    _logger.error("SRI Auto-send failed for %s: %s", move.name, str(e))
                    move.l10n_ec_sri_response = f"Auto-send error: {e}"

        return result
