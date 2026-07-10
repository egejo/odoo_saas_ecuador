# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64

# Tabla 06 del SRI (tipo de identificacion), acotada a lo que aplica a un
# transportista (persona natural o RUC de la transportadora) -- mismo
# catalogo que usa l10n_ec_sri_xml.py para el comprador de facturas, ver
# comentario ahi.
_TIPO_IDENTIFICACION_TRANSPORTISTA = {
    "ruc": "04",
    "cedula": "05",
    "pasaporte": "06",
}

# Las 7 categorias oficiales de motivo de traslado segun la Ficha Tecnica
# del SRI (Manual de usuario, catalogo y especificaciones tecnicas). El
# intento previo del upstream (l10n_ec_stock, nunca instalado -- ver
# __manifest__.py) usaba un set incompleto de 6 opciones y ademas
# transmitia la CLAVE interna de seleccion ("traslado") en vez de un
# texto legible en <motivoTraslado> -- este mapeo corrige ambos problemas.
_TRANSPORT_REASON_LABEL = {
    "venta": "Venta con entrega posterior",
    "traslado": "Traslado entre establecimientos de la misma empresa",
    "consignacion": "Entrega en consignación",
    "devolucion": "Devolución de mercadería",
    "reparacion": "Envío para reparación o mantenimiento",
    "comercio_exterior": "Importación o exportación",
    "exhibicion": "Demostraciones, exposiciones o ferias",
}


class L10nEcDeliveryGuide(models.Model):
    _name = "l10n_ec.delivery.guide"
    _description = "Guía de Remisión (Ecuador)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, name desc"

    name = fields.Char(
        string="Número de Documento",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default="Draft",
    )
    company_id = fields.Many2one(
        "res.company", index=True, required=True, default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    # Muchas guias pueden apuntar al MISMO picking -- a proposito, es lo
    # que permite crear varias guias desde un solo despacho de bodega o
    # transferencia interna (ej. 2 camiones, 2 viajes). No se declara
    # unico ni se restringe por picking_id.state en ningun lado de este
    # modelo: una guia se puede crear con el despacho todavia en 'draft'/
    # 'assigned' o ya en 'done'.
    picking_id = fields.Many2one(
        "stock.picking", string="Despacho de Bodega", required=True, index=True
    )
    partner_id = fields.Many2one("res.partner", string="Destinatario", required=True)
    transport_reason = fields.Selection(
        [(k, v) for k, v in _TRANSPORT_REASON_LABEL.items()],
        string="Motivo del Traslado",
        required=True,
        default="traslado",
    )

    driver_id = fields.Many2one("l10n_ec.driver", string="Transportista", required=True)
    vehicle_id = fields.Many2one("l10n_ec.vehicle", string="Vehículo", required=True)

    date_start = fields.Date(
        string="Fecha Inicio Transporte",
        required=True,
        default=fields.Date.context_today,
        copy=False,
    )
    date_end = fields.Date(
        string="Fecha Fin Transporte",
        required=True,
        default=fields.Date.context_today,
        copy=False,
    )

    dir_partida = fields.Char(string="Dirección de Partida", required=True)
    dir_destino = fields.Char(string="Dirección de Destino", required=True)
    route = fields.Char(string="Ruta")

    # Cuando el motivo es "venta con entrega posterior", vincular la orden
    # de venta que motiva el traslado permite poblar <codDocSustento>/
    # <numDocSustento>/<numAutDocSustento>/<fechaEmisionDocSustento> con
    # los datos de la factura ya autorizada -- ver _get_docsustento_values.
    sale_id = fields.Many2one(
        "sale.order", string="Venta relacionada (Documento Sustento)"
    )

    line_ids = fields.One2many(
        "l10n_ec.delivery.guide.line", "delivery_guide_id", string="Detalle"
    )

    # SRI Integration Fields (mismo patron que account.retention)
    l10n_ec_sri_access_key = fields.Char(string="Clave de Acceso SRI", copy=False)
    l10n_ec_sri_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("signed", "Signed"),
            ("sent", "Sent"),
            ("authorized", "Authorized"),
            ("rejected", "Rejected"),
        ],
        string="Estado SRI",
        default="draft",
        copy=False,
        index=True,
        tracking=True,
    )
    l10n_ec_sri_response = fields.Text("Respuesta SRI")
    l10n_ec_xml_data = fields.Binary("Archivo XML", attachment=True)
    l10n_ec_authorization_date = fields.Datetime(
        string="Fecha de Autorización", copy=False
    )

    @api.model
    def create(self, vals):
        if vals.get("name", "Draft") == "Draft":
            company = self.env["res.company"].browse(
                vals.get("company_id") or self.env.company.id
            )
            estab = company.l10n_ec_delivery_guide_establishment or "001"
            pto = company.l10n_ec_delivery_guide_emission_point or "001"
            seq_number = (
                self.env["ir.sequence"].next_by_code("l10n_ec.delivery.guide")
                or "000000000"
            )
            vals["name"] = f"{estab}-{pto}-{seq_number}"
        return super(L10nEcDeliveryGuide, self).create(vals)

    # =========================================================================
    # REGULACIONES SRI 2026 (Res. NAC-DGERCGC25-00000017)
    # =========================================================================
    # - Transmisión INMEDIATA: la guía debe estar autorizada por el SRI
    #   antes de iniciar el traslado fisico, no despues (ver guard en
    #   action_send_sri sobre date_start).
    # - Anulación solo hasta el dia 7 del mes siguiente a la emision,
    #   igual que el resto de comprobantes de este fork -- con la
    #   particularidad normativa (sin efecto adicional en este metodo) de
    #   que la guia "solo es valida durante el traslado": una vez la
    #   mercaderia llego a destino no tiene sentido anularla
    #   retroactivamente aunque el plazo de 7 dias siga abierto.
    # =========================================================================
    def _check_cancellation_allowed(self):
        from datetime import date

        from odoo.addons.l10n_ec_edi.models.access_key import AccessKey

        self.ensure_one()

        if not self.date_start:
            return True

        today = AccessKey.today_ec()
        emission_date = self.date_start

        if emission_date.month == 12:
            limit_date = date(emission_date.year + 1, 1, 7)
        else:
            limit_date = date(emission_date.year, emission_date.month + 1, 7)

        if today > limit_date:
            raise ValidationError(
                _(
                    "No se puede anular esta guía de remisión.\n\n"
                    "Según Resolución NAC-DGERCGC25-00000017, la anulación solo "
                    "es permitida hasta el día 7 del mes siguiente a la "
                    "emisión.\n\n"
                    "Fecha de emisión: %s\n"
                    "Fecha límite de anulación: %s\n"
                    "Fecha actual: %s"
                )
                % (emission_date, limit_date, today)
            )

        return True

    def action_cancel(self):
        for record in self:
            if record.l10n_ec_sri_status == "authorized":
                record._check_cancellation_allowed()
            record.active = False

    def _generate_access_key(self):
        from odoo.addons.l10n_ec_edi.models.access_key import AccessKey

        for record in self:
            if record.l10n_ec_sri_access_key:
                continue

            env = (
                "2"
                if record.company_id.l10n_ec_sri_environment == "production"
                else "1"
            )

            # El nombre siempre viene de create() con formato
            # "001-001-000000001" (estab-ptoEmi-secuencial).
            parts = record.name.split("-")
            if len(parts) == 3:
                estab, pto, seq = parts
            else:
                estab = record.company_id.l10n_ec_delivery_guide_establishment or "001"
                pto = record.company_id.l10n_ec_delivery_guide_emission_point or "001"
                seq = record.id

            record.l10n_ec_sri_access_key = AccessKey.generate(
                invoice_date=record.date_start,
                doc_type="06",  # Guía de Remisión
                ruc=record.company_id.vat,
                environment=env,
                establishment=estab,
                emission_point=pto,
                sequential=seq,
            )

    def _get_transportista_identification_code(self):
        self.ensure_one()
        return _TIPO_IDENTIFICACION_TRANSPORTISTA.get(
            self.driver_id.identification_type, "05"
        )

    def _get_docsustento_values(self):
        """
        Referencia a la factura de venta que motiva el traslado (cuando
        aplica): <codDocSustento>/<numDocSustento>/<numAutDocSustento>/
        <fechaEmisionDocSustento>, exigidos por el esquema real cuando
        corresponde (Ficha Técnica, pág. 66-67). Devuelve False si no hay
        venta vinculada o la venta todavía no tiene una factura
        autorizada por el SRI -- en ese caso el bloque completo se omite
        del XML (son campos "Obligatorio cuando corresponda", no
        siempre).
        """
        self.ensure_one()
        if not self.sale_id:
            return False
        invoice = self.sale_id.invoice_ids.filtered(
            lambda m: m.state == "posted" and m.l10n_ec_sri_status == "authorized"
        )[:1]
        if not invoice:
            return False
        return {
            "cod_doc_sustento": invoice.l10n_latam_document_type_id.code or "01",
            # A diferencia de account.retention (que le quita los guiones
            # a este mismo dato para SU propio docSustento), el schema
            # real de guiaRemision exige el formato con guiones: el SRI
            # rechazo un envio de prueba con error 35 "ARCHIVO NO CUMPLE
            # ESTRUCTURA XML" citando literalmente el patron esperado
            # '[0-9]{3}-[0-9]{3}-[0-9]{9}' para numDocSustento -- distinto
            # de lo que la Ficha Tecnica sugiere ("Numerico 15") y de lo
            # que retencion necesita para el suyo.
            "num_doc_sustento": (
                invoice.l10n_latam_document_number or invoice.name or ""
            ),
            "num_aut_doc_sustento": invoice.l10n_ec_sri_access_key,
            "fecha_emision_doc_sustento": invoice.invoice_date,
        }

    def action_send_sri(self):
        """
        Genera el XML, lo firma y lo transmite al SRI -- mismo patrón que
        account.retention.action_send_sri (l10n_ec_withholding).
        """
        from odoo.addons.l10n_ec_edi.models.access_key import AccessKey

        for record in self:
            if not record.driver_id or not record.vehicle_id:
                raise UserError(
                    _("Transportista y Vehículo son obligatorios para transmitir al SRI.")
                )
            if not record.line_ids:
                raise UserError(_("Agregue al menos una línea de detalle."))

            # Transmisión inmediata (Res. NAC-DGERCGC25-00000017): la
            # fecha de inicio de transporte (que también es la fecha de
            # emisión embebida en la clave de acceso, ya que <guiaRemision>
            # no tiene un tag <fechaEmision> propio) debe ser HOY según el
            # calendario de Ecuador. Evita los errores 65 ("fecha de
            # emisión extemporánea") y 82 ("fecha de inicio de transporte
            # menor a la fecha de emisión") documentados en la Ficha
            # Técnica del SRI.
            if record.date_start != AccessKey.today_ec():
                raise UserError(
                    _(
                        "La Fecha de Inicio de Transporte debe ser hoy (%s) según "
                        "el calendario de Ecuador -- el SRI exige transmitir la "
                        "guía de remisión antes de iniciar el traslado físico, el "
                        "mismo día. Actualice la fecha antes de enviar."
                    )
                    % AccessKey.today_ec()
                )

            if not record.l10n_ec_sri_access_key:
                record._generate_access_key()

            docsustento = record._get_docsustento_values()

            values = {
                "guide": record,
                "company": record.company_id,
                "environment": (
                    "1" if record.company_id.l10n_ec_sri_environment == "test" else "2"
                ),
                "access_key": record.l10n_ec_sri_access_key,
                "format_float": lambda x, p=2: ("%." + str(p) + "f") % x,
                "transportista_identification_code": record._get_transportista_identification_code(),
                "motivo_traslado_label": _TRANSPORT_REASON_LABEL.get(
                    record.transport_reason, record.transport_reason
                ),
                "docsustento": docsustento,
            }
            xml_content = self.env["ir.qweb"]._render(
                "l10n_ec_delivery_guide.l10n_ec_delivery_guide_xml", values
            )

            certificate = record.company_id.l10n_ec_certificate_id
            if not certificate or certificate.state != "active":
                raise UserError(
                    _("SRI Error: No active Signing Certificate configured.")
                )

            try:
                signer = self.env["l10n_ec.sri.signer"]
                service = self.env["l10n_ec.sri.service"]

                signed_xml_bytes = signer.sign_xml(
                    xml_content.encode("utf-8"),
                    certificate.content,
                    certificate.password,
                )

                env_code = (
                    "1" if record.company_id.l10n_ec_sri_environment == "test" else "2"
                )
                response_data = service.send_document(signed_xml_bytes, env_code)

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

    def action_check_sri(self):
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
        self.ensure_one()
        if not self.l10n_ec_xml_data:
            return self.env["ir.attachment"]
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "l10n_ec.delivery.guide"),
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
                    % (self.l10n_ec_sri_access_key or self.name or "guia_remision"),
                    "mimetype": "application/xml",
                }
            )
        return attachment

    def action_send_by_email(self):
        """
        Envía el RIDE (PDF) y el XML autorizado al destinatario. Mismo
        patrón y misma base normativa (Resolución NAC-DGERCGC18-00000233,
        Art. 6) que account.retention.action_send_by_email -- entregar
        solo uno de los dos archivos "constituye falta de entrega".
        """
        self.ensure_one()
        if self.l10n_ec_sri_status != "authorized":
            raise UserError(
                _(
                    "La guía debe estar Autorizada por el SRI antes de "
                    "enviarla por correo."
                )
            )

        report = self.env.ref("l10n_ec_delivery_guide.action_report_delivery_guide")
        pdf_content, _unused = report._render_qweb_pdf(report.report_name, self.ids)
        pdf_attachment = self.env["ir.attachment"].create(
            {
                "name": "%s.pdf" % (self.name or "guia_remision"),
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": "l10n_ec.delivery.guide",
                "res_id": self.id,
                "mimetype": "application/pdf",
            }
        )
        attachment_ids = [pdf_attachment.id]
        xml_attachment = self._l10n_ec_get_xml_attachment()
        if xml_attachment:
            attachment_ids.append(xml_attachment.id)

        compose_form = self.env.ref("mail.email_compose_message_wizard_form")
        template = self.env.ref(
            "l10n_ec_delivery_guide.mail_template_delivery_guide",
            raise_if_not_found=False,
        )
        ctx = {
            "default_model": "l10n_ec.delivery.guide",
            "default_res_ids": self.ids,
            "default_partner_ids": [self.partner_id.id],
            "default_subject": _("Guía de Remisión %s") % (self.name or ""),
            "default_attachment_ids": attachment_ids,
            "default_composition_mode": "comment",
        }
        if template:
            ctx["default_template_id"] = template.id
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
