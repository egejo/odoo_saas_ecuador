# -*- coding: utf-8 -*-
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
