# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def l10n_ec_pos_invoice_and_send(self):
        """
        Factura esta orden de POS (si todavia no tiene account_move) y la
        transmite al SRI (RECIBIDA/rechazada). No espera aqui a que el SRI
        la autorice -- eso lo hace el frontend llamando repetidamente a
        l10n_ec_pos_check_sri, para no bloquear un worker de Odoo con
        time.sleep durante los ~10-15s que tarda la autorizacion real.

        Reemplaza el mecanismo viejo de este modulo (_generate_pos_access_key
        en pos.order.create()): generaba una clave de acceso propia que
        nunca se firmaba ni transmitia, y quedaba huerfana -- la factura
        real de la orden vive en account_move, con su propio
        l10n_ec_sri_access_key ya probado end-to-end contra el SRI.
        """
        self.ensure_one()
        if not self.config_id.l10n_ec_sri_active:
            return {}

        if not self.partner_id:
            default_partner = self.config_id.l10n_ec_default_partner_id
            if not default_partner:
                raise UserError(
                    _(
                        "Configure un Cliente por Defecto (Consumidor Final) en "
                        "Punto de Venta > Configuracion > Ecuador SRI para poder "
                        "facturar automaticamente."
                    )
                )
            self.partner_id = default_partner

        if not self.account_move:
            self.with_context(generate_pdf=False).action_pos_order_invoice()

        move = self.account_move
        if move and move.l10n_ec_sri_status == "draft":
            try:
                move.action_send_sri()
            except UserError as exc:
                _logger.warning(
                    "l10n_ec_pos: SRI rechazo la factura %s de la orden %s: %s",
                    move.name, self.name, exc,
                )

        return self._l10n_ec_pos_sri_receipt_data()

    def l10n_ec_pos_check_sri(self):
        """Sondea el estado de autorizacion; se llama repetidamente desde el
        frontend (con espera entre llamadas del lado del navegador, no del
        worker) hasta que el SRI autoriza/rechaza o se agotan los intentos.
        """
        self.ensure_one()
        move = self.account_move
        if move and move.l10n_ec_sri_status == "sent":
            move.action_check_sri()
        return self._l10n_ec_pos_sri_receipt_data()

    def _l10n_ec_pos_sri_receipt_data(self):
        self.ensure_one()
        move = self.account_move
        if not move:
            return {}
        partner = move.partner_id
        return {
            "move_name": move.name,
            "l10n_ec_sri_status": move.l10n_ec_sri_status,
            "l10n_ec_sri_access_key": move.l10n_ec_sri_access_key,
            "l10n_ec_authorization_date": (
                fields.Datetime.to_string(move.l10n_ec_authorization_date)
                if move.l10n_ec_authorization_date
                else False
            ),
            "l10n_ec_sri_error": move.l10n_ec_sri_error,
            "invoice_date": (
                fields.Date.to_string(move.invoice_date) if move.invoice_date else False
            ),
            "document_type": move.l10n_latam_document_type_id.name or _("Factura"),
            "company_street": move.company_id.street or "",
            "partner_name": partner.name or _("Consumidor Final"),
            "partner_vat": partner.vat or "",
            "partner_identification_type": partner.l10n_latam_identification_type_id.name or "",
        }
