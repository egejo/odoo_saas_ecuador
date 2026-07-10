# -*- coding: utf-8 -*-
from odoo import models, fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # One2many de solo lectura hacia las guías ya creadas sobre este
    # picking -- puede haber mas de una a proposito (ver
    # l10n_ec.delivery.guide.picking_id). Sirve para el smart button y
    # para que el wizard sepa que ya se emitieron guias antes.
    l10n_ec_delivery_guide_ids = fields.One2many(
        "l10n_ec.delivery.guide", "picking_id", string="Guías de Remisión"
    )
    l10n_ec_delivery_guide_count = fields.Integer(
        compute="_compute_l10n_ec_delivery_guide_count"
    )

    def _compute_l10n_ec_delivery_guide_count(self):
        for picking in self:
            picking.l10n_ec_delivery_guide_count = len(
                picking.l10n_ec_delivery_guide_ids
            )

    def action_create_delivery_guide(self):
        self.ensure_one()
        return {
            "name": "Crear Guía de Remisión",
            "type": "ir.actions.act_window",
            "res_model": "l10n_ec.delivery.guide.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "stock.picking",
                "active_id": self.id,
            },
        }

    def action_view_delivery_guides(self):
        self.ensure_one()
        action = {
            "name": "Guías de Remisión",
            "type": "ir.actions.act_window",
            "res_model": "l10n_ec.delivery.guide",
            "domain": [("picking_id", "=", self.id)],
            "context": {"default_picking_id": self.id},
        }
        if self.l10n_ec_delivery_guide_count == 1:
            action["view_mode"] = "form"
            action["res_id"] = self.l10n_ec_delivery_guide_ids.id
        else:
            action["view_mode"] = "list,form"
        return action
