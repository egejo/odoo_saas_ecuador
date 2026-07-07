# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, _
from odoo.exceptions import UserError
import base64


class AccountMove(models.Model):
    """
    Extends account.move with SRI integration logic.
    Field definitions inherited from l10n_ec_edi.

    Note: 2026 Consumidor Final validations are handled by l10n_ec_edi module.
    """

    _inherit = "account.move"

    # Additional fields not in l10n_ec_edi
    l10n_ec_authorization_date = fields.Datetime(
        string="Authorization Date", copy=False
    )
    l10n_ec_sri_error = fields.Text(string="SRI Error Message", copy=False)
    l10n_ec_sri_additional_info = fields.Text(
        string="Información Adicional (RIDE)",
        help="Texto libre que se imprime en el bloque \"Información "
        "Adicional\" del RIDE. El usuario lo completa manualmente antes "
        "de emitir el comprobante, si lo necesita (no se genera "
        "automáticamente).",
    )

    def action_send_sri(self):
        """
        Orchestrator: Key Gen -> XML Gen -> Sign -> Send
        """
        for move in self:
            if move.l10n_ec_sri_status in ["authorized", "sent"]:
                continue

            # 1. Generate Access Key
            if not move.l10n_ec_sri_access_key:
                move.l10n_ec_sri_access_key = self.env[
                    "l10n_ec.sri.xml"
                ].generate_access_key(move)

            # 2. Render XML
            xml_content = self.env["l10n_ec.sri.xml"].render_xml(move)
            if not isinstance(xml_content, bytes):
                xml_content = xml_content.encode("utf-8")

            # 3. Sign XML
            signed_xml = self._sign_xml(xml_content)
            move.l10n_ec_xml_data = base64.b64encode(signed_xml)

            # 4. Send to SRI (Real Call)
            response = self.env["l10n_ec.sri.service"].send_document(
                signed_xml, environment=move.company_id.l10n_ec_sri_environment
            )

            if response.get("status") == "RECIBIDA":
                move.l10n_ec_sri_status = "sent"
                move.l10n_ec_sri_error = False
            else:
                move.l10n_ec_sri_status = "rejected"
                move.l10n_ec_sri_error = "\n".join(response.get("messages", []))

    def action_check_sri(self):
        """
        Ping Check Status service (Real Implementation)
        """
        for move in self:
            if not move.l10n_ec_sri_access_key:
                raise UserError(_("No Access Key generated yet."))

            response = self.env["l10n_ec.sri.service"].check_authorization(
                move.l10n_ec_sri_access_key
            )

            if response.get("status") == "AUTORIZADO":
                move.l10n_ec_sri_status = "authorized"
                if response.get("date"):
                    move.l10n_ec_authorization_date = response["date"]

                if response.get("authorized_xml"):
                    move.l10n_ec_xml_data = base64.b64encode(
                        response["authorized_xml"].encode("utf-8")
                    )
            elif response.get("status") == "NO AUTORIZADO":
                move.l10n_ec_sri_status = "rejected"
                move.l10n_ec_sri_error = "\n".join(response.get("messages", []))

    def _l10n_ec_get_payment_data(self):
        """
        Forma de pago para el RIDE (l10n_ec_sri_payment_id existe en el
        account.move core desde el modulo l10n_ec, pero nunca se expone en
        ninguna vista ni se usa en ningun reporte: sin esto, la factura
        impresa nunca puede mostrar como se pago, aunque el campo ya este
        ahi).
        """
        self.ensure_one()
        pay_term_lines = self.line_ids.filtered(
            lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable")
        )
        payment_name = self.l10n_ec_sri_payment_id.name or _("Sin especificar")
        return [
            {"payment_name": payment_name, "payment_total": abs(line.balance)}
            for line in pay_term_lines
        ]

    def _l10n_ec_get_invoice_additional_info(self):
        """
        Bloque "Informacion Adicional" del RIDE: vendedor (dato ya
        disponible en toda factura) y el correo del cliente registrado
        (a donde el SRI/Odoo remite el comprobante electronico) mas lo
        que el usuario haya escrito a mano en l10n_ec_sri_additional_info.
        El telefono del cliente NO va aqui: se muestra en el bloque de
        identificacion del cliente, junto a RUC/Fecha Emision/Vence.
        """
        self.ensure_one()
        return {
            _("Vendedor"): self.invoice_user_id.name or "",
            _("Correo"): self.partner_id.email or "",
        }

    def _l10n_ec_get_ride_totals(self):
        """
        Desglose de totales del RIDE (Subtotal 0%/5%/15%, No Objeto de
        IVA, Exento de IVA, ICE, IVA 5%/15%, etc.), agrupado por
        l10n_ec_type del grupo de impuesto de cada linea -- el mismo
        campo que l10n_ec.sri.xml usa para clasificar impuestos en el
        XML firmado (tabla17/tabla18 del SRI). Se reutiliza esa misma
        clasificacion aqui para que el PDF impreso nunca muestre un
        desglose distinto al que realmente se envio al SRI.
        """
        self.ensure_one()
        bases = defaultdict(float)
        amounts = defaultdict(float)

        for line in self.invoice_line_ids.filtered(
            lambda l: l.display_type == "product"
        ):
            for tax in line.tax_ids:
                bases[tax.tax_group_id.l10n_ec_type] += line.price_subtotal

        for line in self.line_ids.filtered(lambda l: l.tax_line_id):
            amounts[line.tax_line_id.tax_group_id.l10n_ec_type] += abs(line.balance)

        # Sin mecanismo de descuento global/de cabecera en este sistema
        # (el descuento por linea ya esta incluido en price_subtotal):
        # Descuento siempre 0.00, Subtotal Neto == Subtotal.
        return {
            "subtotal": self.amount_untaxed,
            "descuento": 0.0,
            "subtotal_neto": self.amount_untaxed,
            "subtotal_5": bases.get("vat05", 0.0),
            "subtotal_15": bases.get("vat15", 0.0),
            "subtotal_0": bases.get("zero_vat", 0.0),
            "subtotal_no_objeto": bases.get("not_charged_vat", 0.0),
            "subtotal_exento": bases.get("exempt_vat", 0.0),
            "ice": amounts.get("ice", 0.0),
            "iva_5": amounts.get("vat05", 0.0),
            "iva_15": amounts.get("vat15", 0.0),
            "propina": 0.0,
            "valor_total": self.amount_total,
        }

    def _get_name_invoice_report(self):
        # EXTENDS account_move
        # Sin esto, Odoo siempre imprime account.report_invoice_document
        # (el layout generico) sin clave de acceso, numero de autorizacion,
        # ni codigo de barras: no es un RIDE valido ante el SRI. Solo se activa
        # para los tipos de documento que realmente se firman/envian hoy
        # (factura y nota de credito, ver l10n_ec.sri.xml.render_xml); el
        # resto (nota de debito, guia de remision, etc.) sigue sin RIDE hasta
        # que su generacion de XML este implementada.
        self.ensure_one()
        if (
            self.l10n_latam_use_documents
            and self.country_code == "EC"
            and self.l10n_latam_document_type_id.code in ("01", "04")
        ):
            return "l10n_ec_sri.report_invoice_document"
        return super()._get_name_invoice_report()

    def _sign_xml(self, xml_content):
        """
        Internal helper to call the signer lib.
        """
        self.ensure_one()
        certificate = self.company_id.l10n_ec_certificate_id
        if not certificate:
            raise UserError(_("No active Electronic Signature found for this company."))

        return self.env["l10n_ec.sri.signer"].sign_xml(
            xml_content, certificate.content, certificate.password
        )
