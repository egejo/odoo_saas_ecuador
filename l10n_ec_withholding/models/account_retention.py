# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64

# Tabla 06 del SRI (tipo de identificacion). Mismo mapeo que
# l10n_ec_sri_xml.py usa para el comprador de facturas -- se duplica aqui
# en vez de importar esa constante de l10n_ec_sri (aunque este modulo ya
# depende de el para el layout del RIDE, ver report/report_retention.xml)
# porque es un catalogo SRI estable de 4 lineas, no vale la pena acoplar
# el import a la estructura interna de l10n_ec_sri_xml.py.
_TIPO_IDENTIFICACION_SUJETO_RETENIDO = {
    "ruc": "04",
    "cedula": "05",
    "ec_passport": "06",
    "passport": "06",
    "foreign": "08",
}
# Tabla 16 del SRI (codigo de impuesto en <retenciones><retencion><codigo>):
# 1=Renta, 2=IVA, 6=ISD. account.retention.line.tax_type usa el mismo
# vocabulario que l10n_ec.withholding.tax.type ("renta"/"iva"/"isd"), asi
# que hace falta este mapeo para el XML.
_RETENTION_TAX_TYPE_CODE = {"renta": "1", "iva": "2", "isd": "6"}
# Tabla 17/18 del SRI, para los impuestos DE LA FACTURA SUSTENO
# (impuestosDocSustento) -- no confundir con los impuestos retenidos. Es
# el mismo mapeo que l10n_ec_sri_xml.py usa para el XML de facturas.
_TABLA17_CODIGO_IMPUESTO = {
    "vat05": "2", "vat08": "2", "vat12": "2", "vat13": "2", "vat14": "2",
    "vat15": "2", "zero_vat": "2", "not_charged_vat": "2", "exempt_vat": "2",
    "ice": "3",
    "irbpnr": "5",
}
_TABLA18_CODIGO_PORCENTAJE = {
    "zero_vat": "0",
    "not_charged_vat": "6",
    "exempt_vat": "7",
    "vat05": "5",
    "vat12": "2",
    "vat14": "3",
    "vat15": "4",
}


class AccountRetention(models.Model):
    _name = "account.retention"
    _description = "Comprobante de Retención (Ecuador)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, name desc"

    name = fields.Char(
        string="Document Number",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default="Draft",
    )
    company_id = fields.Many2one(
        "res.company", index=True, required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    partner_id = fields.Many2one(
        "res.partner", string="Vendor", required=True, index=True
    )
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)

    # SRI Integration Fields (Direct Link to Shared Logic)
    l10n_ec_sri_access_key = fields.Char(string="SRI Access Key", copy=False)
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
        tracking=True,
    )
    l10n_ec_sri_response = fields.Text("SRI Response")
    l10n_ec_xml_data = fields.Binary("XML File", attachment=True)
    l10n_ec_authorization_date = fields.Datetime(
        string="Authorization Date", copy=False
    )

    # Lines
    retention_line_ids = fields.One2many(
        "account.retention.line", "retention_id", string="Withholding Lines"
    )

    invoice_id = fields.Many2one(
        "account.move", string="Related Bill", domain=[("move_type", "=", "in_invoice")]
    )

    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("cancel", "Cancelled")],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # =========================================================================
    # REGULACIONES SRI 2026 (Res. NAC-DGERCGC25-00000017)
    # =========================================================================
    # - Transmisión INMEDIATA de comprobantes electrónicos
    # - Anulación permitida hasta día 7 del mes siguiente
    # - Anulación requiere aceptación del receptor en 5 días hábiles
    # - La regla de 5 días para retención YA NO APLICA desde 2026
    # =========================================================================

    def _check_cancellation_allowed(self):
        """
        Valida si el documento puede ser anulado según regulaciones SRI 2026.

        Regla: Anulación solo hasta el día 7 del mes siguiente a la emisión.
        Resolución NAC-DGERCGC25-00000017
        """
        from datetime import date

        self.ensure_one()

        if not self.date:
            return True

        today = date.today()
        emission_date = self.date

        # Calcular fecha límite: día 7 del mes siguiente
        if emission_date.month == 12:
            limit_date = date(emission_date.year + 1, 1, 7)
        else:
            limit_date = date(emission_date.year, emission_date.month + 1, 7)

        if today > limit_date:
            raise ValidationError(
                _(
                    "No se puede anular este documento.\n\n"
                    "Según Resolución NAC-DGERCGC25-00000017, la anulación solo es "
                    "permitida hasta el día 7 del mes siguiente a la emisión.\n\n"
                    "Fecha de emisión: %s\n"
                    "Fecha límite de anulación: %s\n"
                    "Fecha actual: %s"
                )
                % (emission_date, limit_date, today)
            )

        return True

    @api.constrains("date", "invoice_id")
    def _check_retention_date(self):
        """
        Valida que la fecha de retención sea coherente con la factura.

        NOTA: La regla de 5 días fue ELIMINADA en 2026.
        Solo validamos que la fecha no sea anterior a la factura.
        """
        for record in self:
            if record.invoice_id and record.date:
                inv_date = record.invoice_id.invoice_date
                if not inv_date:
                    continue
                if record.date < inv_date:
                    raise ValidationError(
                        _(
                            "La fecha de retención (%s) no puede ser anterior "
                            "a la fecha de la factura (%s)."
                        )
                        % (record.date, inv_date)
                    )

    @api.model
    def create(self, vals):
        if vals.get("name", "Draft") == "Draft":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("account.retention") or "Draft"
            )
        return super(AccountRetention, self).create(vals)

    def action_post(self):
        self.write({"state": "posted"})
        # Trigger SRI flow here in future

    def _generate_access_key(self):
        """
        Genera la clave de acceso usando el helper compartido de
        l10n_ec_edi (mismo algoritmo modulo 11 que usa l10n_ec_sri, solo
        que expuesto ahi como clase Python en vez de metodo de modelo).
        """
        from odoo.addons.l10n_ec_edi.models.access_key import AccessKey

        for record in self:
            if record.l10n_ec_sri_access_key:
                continue

            env = (
                "2"
                if record.company_id.l10n_ec_sri_environment == "production"
                else "1"
            )

            # Formato esperado del nombre: "001-001-000000001" (ver
            # data/l10n_ec_withholding.xml: prefix="001-001-", padding=9).
            parts = record.name.split("-")
            if len(parts) == 3:
                estab, pto, seq = parts
            else:
                estab, pto = "001", "001"
                seq = record.id

            record.l10n_ec_sri_access_key = AccessKey.generate(
                invoice_date=record.date,
                doc_type="07",  # Comprobante de Retencion
                ruc=record.company_id.vat,
                environment=env,
                establishment=estab,
                emission_point=pto,
                sequential=seq,
            )

    def _get_invoice_tax_breakdown(self, invoice):
        """
        Desglose de los impuestos DE LA FACTURA SUSTENTO (no de la
        retencion), para <impuestosDocSustento> -- el SRI exige mostrar
        ahi los impuestos originales de la factura que se esta
        retención, ademas de los valores retenidos en <retenciones>.
        Misma clasificacion por l10n_ec_type que usa l10n_ec_sri_xml.py
        para las facturas.
        """
        breakdown = []
        for line in invoice.line_ids.filtered(lambda l: l.tax_line_id):
            ec_type = line.tax_line_id.tax_group_id.l10n_ec_type
            if ec_type not in _TABLA17_CODIGO_IMPUESTO:
                continue
            breakdown.append(
                {
                    "codigo": _TABLA17_CODIGO_IMPUESTO[ec_type],
                    "codigo_porcentaje": _TABLA18_CODIGO_PORCENTAJE.get(ec_type, "0"),
                    "tarifa": line.tax_line_id.amount,
                    "base_imponible": abs(line.tax_base_amount),
                    "valor": abs(line.balance),
                }
            )
        return breakdown

    def action_send_sri(self):
        """
        Generates XML, Signs it, and Sends to SRI.
        """
        for record in self:
            if not record.l10n_ec_sri_access_key:
                record._generate_access_key()

            invoice = record.invoice_id
            partner_type = record.partner_id._l10n_ec_get_identification_type()

            # 1. Render XML
            values = {
                "retention": record,
                "company": record.company_id,
                "partner": record.partner_id,
                "environment": (
                    "1" if record.company_id.l10n_ec_sri_environment == "test" else "2"
                ),
                "access_key": record.l10n_ec_sri_access_key,
                "format_monetary": lambda x: "%.2f" % x,
                "format_float": lambda x, p: ("%." + str(p) + "f") % x,
                "identifier_code": _TIPO_IDENTIFICACION_SUJETO_RETENIDO.get(
                    partner_type, "05"
                ),
                "retention_tax_type_code": _RETENTION_TAX_TYPE_CODE,
                "invoice_sustento_code": invoice.l10n_ec_sustento_code or "01",
                "invoice_doc_type_code": invoice.l10n_latam_document_type_id.code
                or "01",
                "invoice_doc_number": (
                    invoice.l10n_latam_document_number or invoice.name or ""
                ).replace("-", ""),
                "invoice_doc_date": (
                    invoice.invoice_date.strftime("%d/%m/%Y")
                    if invoice.invoice_date
                    else ""
                ),
                "invoice_tax_breakdown": record._get_invoice_tax_breakdown(invoice),
                "invoice_payment_code": invoice.l10n_ec_sri_payment_id.code or "01",
            }
            xml_content = self.env["ir.qweb"]._render(
                "l10n_ec_withholding.l10n_ec_retention_xml", values
            )

            # 2. Sign
            certificate = record.company_id.l10n_ec_certificate_id
            if not certificate or certificate.state != "active":
                raise UserError(
                    _("SRI Error: No active Signing Certificate configured.")
                )

            try:
                # Use AbstractModels from l10n_ec_edi
                signer = self.env["l10n_ec.sri.signer"]
                service = self.env["l10n_ec.sri.service"]

                signed_xml_bytes = signer.sign_xml(
                    xml_content.encode("utf-8"),
                    certificate.content,
                    certificate.password,
                )

                # 3. Transmit
                env_code = (
                    "1" if record.company_id.l10n_ec_sri_environment == "test" else "2"
                )
                response_data = service.send_document(signed_xml_bytes, env_code)

                # 4. Process
                if response_data.get("status") == "RECIBIDA":
                    record.l10n_ec_sri_status = "sent"
                    record.l10n_ec_sri_response = (
                        "RECIBIDA. Waiting for Authorization..."
                    )
                else:
                    record.l10n_ec_sri_status = "rejected"
                    msgs = "\n".join(response_data.get("messages", []))
                    record.l10n_ec_sri_response = (
                        f"{response_data.get('status')}: {msgs}"
                    )

                record.l10n_ec_xml_data = base64.b64encode(signed_xml_bytes)

            except Exception as e:
                record.l10n_ec_sri_response = f"System Error: {str(e)}"
                # Don't rollback, save the error

    def action_check_sri(self):
        """
        Consulta el estado de autorizacion en el SRI. Sin esto, el
        comprobante quedaba atascado en 'sent' para siempre -- nunca
        habia forma de confirmar 'AUTORIZADO' (a diferencia del flujo de
        facturas en l10n_ec_sri, que si tiene action_check_sri).
        """
        for record in self:
            if not record.l10n_ec_sri_access_key:
                raise UserError(_("No Access Key generated yet."))

            response = self.env["l10n_ec.sri.service"].check_authorization(
                record.l10n_ec_sri_access_key
            )

            if response.get("status") == "AUTORIZADO":
                record.l10n_ec_sri_status = "authorized"
                if response.get("date"):
                    record.l10n_ec_authorization_date = response["date"]
            elif response.get("status") == "NO AUTORIZADO":
                record.l10n_ec_sri_status = "rejected"
                record.l10n_ec_sri_response = "\n".join(
                    response.get("messages", [])
                )

    def _l10n_ec_get_xml_attachment(self):
        """
        ir.attachment del XML firmado/autorizado. l10n_ec_xml_data (Binary
        con attachment=True) ya crea automaticamente un ir.attachment al
        asignarle un valor, pero sin nombre/mimetype utiles para
        adjuntarlo al correo del proveedor (mismo patron que
        account.move._l10n_ec_get_xml_attachment en l10n_ec_sri).
        """
        self.ensure_one()
        if not self.l10n_ec_xml_data:
            return self.env["ir.attachment"]
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.retention"),
                ("res_id", "=", self.id),
                ("res_field", "=", "l10n_ec_xml_data"),
            ],
            limit=1,
        )
        if attachment and (
            attachment.mimetype != "application/xml"
            or not attachment.name.endswith(".xml")
        ):
            attachment.write(
                {
                    "name": "%s.xml"
                    % (self.l10n_ec_sri_access_key or self.name or "retencion"),
                    "mimetype": "application/xml",
                }
            )
        return attachment

    def action_send_by_email(self):
        """
        Envia el RIDE (PDF) y el XML autorizado al correo del proveedor.

        Normativa vigente (Resolucion NAC-DGERCGC18-00000233, Art. 6
        "Entrega de comprobantes electronicos", ver l10n_ec_sri/models/
        account_move_send.py para el mismo requisito aplicado a
        facturas): el comprobante electronico -- cualquiera de los tipos
        que cubre esa resolucion, incluido el comprobante de retencion --
        solo se entiende entregado cuando se envian AMBOS archivos (XML y
        RIDE) al correo del receptor; enviar solo uno "constituye falta
        de entrega" segun el mismo articulo. account.retention no hereda
        de account.move, asi que no puede reusar el asistente "Enviar e
        Imprimir" (account.move.send): se abre el compositor de correo
        generico de Odoo con ambos adjuntos ya preparados.
        """
        self.ensure_one()
        if self.l10n_ec_sri_status != "authorized":
            raise UserError(
                _(
                    "El comprobante debe estar Autorizado por el SRI antes de "
                    "enviarlo por correo."
                )
            )

        report = self.env.ref("l10n_ec_withholding.action_report_retention")
        pdf_content, _unused = report._render_qweb_pdf(report.report_name, self.ids)
        pdf_attachment = self.env["ir.attachment"].create(
            {
                "name": "%s.pdf" % (self.name or "retencion"),
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": "account.retention",
                "res_id": self.id,
                "mimetype": "application/pdf",
            }
        )
        attachment_ids = [pdf_attachment.id]
        xml_attachment = self._l10n_ec_get_xml_attachment()
        if xml_attachment:
            attachment_ids.append(xml_attachment.id)

        compose_form = self.env.ref("mail.email_compose_message_wizard_form")
        ctx = {
            "default_model": "account.retention",
            "default_res_ids": self.ids,
            "default_partner_ids": [self.partner_id.id],
            "default_subject": _("Comprobante de Retención %s") % (self.name or ""),
            "default_attachment_ids": attachment_ids,
            "default_composition_mode": "comment",
        }
        return {
            "name": _("Enviar por Correo"),
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }
