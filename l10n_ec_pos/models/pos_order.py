# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    # SRI Integration Fields
    l10n_ec_sri_access_key = fields.Char(
        string="SRI Access Key", copy=False, help="49-digit Access Key"
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

    l10n_ec_authorization_date = fields.Datetime(
        string="Authorization Date", copy=False
    )

    def _generate_pos_access_key(self):
        """
        Implementation of Access Key Generator specifically for POS.
        Uses the shared l10n_ec_edi logic but adapts for POS session sequences.
        """
        for order in self:
            if not order.l10n_ec_sri_access_key:
                from odoo.addons.l10n_ec_edi.models.access_key import AccessKey

                env = (
                    "2"
                    if order.company_id.l10n_ec_sri_environment == "production"
                    else "1"
                )

                # POS Sequence handling is unique.
                # We use the config's emission point.

                # Sequence: For POS, we often use the 'name' or an internal sequence.
                # Let's clean the name 'Order 00001-001-0001' to get the last part.
                seq_raw = order.pos_reference or order.name or "0"
                # Extract digits
                seq_num = "".join(filter(str.isdigit, seq_raw))[-9:] or str(
                    order.id
                ).zfill(9)

                key = AccessKey.generate(
                    invoice_date=order.date_order.date(),
                    doc_type="01",  # Factura
                    ruc=order.company_id.vat,
                    environment=env,
                    establishment=order.config_id.l10n_ec_entity or "001",
                    emission_point=order.config_id.l10n_ec_emission_point or "001",
                    sequential=seq_num,
                )
                order.l10n_ec_sri_access_key = key

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.config_id.l10n_ec_sri_active and not order.l10n_ec_sri_access_key:
                order._generate_pos_access_key()
        return orders
