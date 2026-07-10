# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..models.l10n_ec_delivery_guide import _TRANSPORT_REASON_LABEL


class L10nEcDeliveryGuideWizard(models.TransientModel):
    _name = "l10n_ec.delivery.guide.wizard"
    _description = "Wizard para Crear Guía de Remisión"

    picking_id = fields.Many2one(
        "stock.picking", string="Despacho de Bodega", required=True
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
        string="Fecha Inicio Transporte", default=fields.Date.context_today, required=True
    )
    date_end = fields.Date(
        string="Fecha Fin Transporte", default=fields.Date.context_today, required=True
    )
    dir_partida = fields.Char(string="Dirección de Partida", required=True)
    dir_destino = fields.Char(string="Dirección de Destino", required=True)
    route = fields.Char(string="Ruta")
    sale_id = fields.Many2one("sale.order", string="Venta relacionada (Documento Sustento)")

    line_ids = fields.One2many(
        "l10n_ec.delivery.guide.wizard.line", "wizard_id", string="Líneas"
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if (
            self.env.context.get("active_model") != "stock.picking"
            or not self.env.context.get("active_id")
        ):
            return res

        picking = self.env["stock.picking"].browse(self.env.context["active_id"])
        res["picking_id"] = picking.id
        if picking.partner_id:
            res["partner_id"] = picking.partner_id.id
            res["dir_destino"] = picking.partner_id._display_address(
                without_company=True
            )

        warehouse_partner = picking.picking_type_id.warehouse_id.partner_id
        res["dir_partida"] = (
            warehouse_partner._display_address(without_company=True)
            if warehouse_partner
            else picking.company_id.partner_id._display_address(without_company=True)
        )

        # Sugerencia de motivo: venta con entrega posterior si el
        # despacho viene de una orden de venta (sale_stock agrega
        # sale_line_id a stock.move); traslado entre establecimientos si
        # es una transferencia interna. En cualquier otro caso se deja
        # el default "traslado" y el usuario ajusta a mano -- no vale la
        # pena adivinar mas alla de estos dos casos, que son los que
        # describio el usuario explicitamente (despacho de bodega /
        # transferencia interna).
        sale_orders = picking.move_ids.sale_line_id.order_id
        if sale_orders:
            res["transport_reason"] = "venta"
            res["sale_id"] = sale_orders[0].id
        elif picking.picking_type_id.code == "internal":
            res["transport_reason"] = "traslado"

        # Una linea por cada stock.move.line ya reservado/hecho -- es lo
        # que permite al usuario borrar/ajustar filas puntuales (por
        # lote/serie) para repartir la carga en varias guias. Si el
        # picking todavia no tiene move_line_ids (muy en borrador, sin
        # reservar), se cae a una linea por stock.move con la cantidad
        # demandada.
        lines = []
        move_lines = picking.move_line_ids
        if move_lines:
            for move_line in move_lines:
                lines.append(
                    (
                        0,
                        0,
                        {
                            "move_line_id": move_line.id,
                            "product_id": move_line.product_id.id,
                            "quantity": move_line.quantity,
                            "uom_id": move_line.product_uom_id.id,
                        },
                    )
                )
        else:
            for move in picking.move_ids:
                lines.append(
                    (
                        0,
                        0,
                        {
                            "move_id": move.id,
                            "product_id": move.product_id.id,
                            "quantity": move.product_uom_qty,
                            "uom_id": move.product_uom.id,
                        },
                    )
                )
        res["line_ids"] = lines
        return res

    def action_create_guide(self):
        self.ensure_one()
        if not any(line.quantity > 0 for line in self.line_ids):
            raise UserError(_("Agregue al menos una línea con cantidad mayor a 0."))

        grouped = {}
        for line in self.line_ids:
            if line.quantity <= 0:
                continue
            data = grouped.setdefault(
                line.product_id.id,
                {
                    "product_id": line.product_id.id,
                    "quantity": 0.0,
                    "uom_id": line.uom_id.id,
                    "move_line_ids": set(),
                },
            )
            data["quantity"] += line.quantity
            if line.move_line_id:
                data["move_line_ids"].add(line.move_line_id.id)

        guide_line_vals = [
            (
                0,
                0,
                {
                    "product_id": v["product_id"],
                    "quantity": v["quantity"],
                    "uom_id": v["uom_id"],
                    "move_line_ids": [(6, 0, sorted(v["move_line_ids"]))],
                },
            )
            for v in grouped.values()
        ]

        guide = self.env["l10n_ec.delivery.guide"].create(
            {
                "picking_id": self.picking_id.id,
                "partner_id": self.partner_id.id,
                "transport_reason": self.transport_reason,
                "driver_id": self.driver_id.id,
                "vehicle_id": self.vehicle_id.id,
                "date_start": self.date_start,
                "date_end": self.date_end,
                "dir_partida": self.dir_partida,
                "dir_destino": self.dir_destino,
                "route": self.route,
                "sale_id": self.sale_id.id if self.sale_id else False,
                "company_id": self.picking_id.company_id.id,
                "line_ids": guide_line_vals,
            }
        )

        return {
            "name": _("Guía de Remisión"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_ec.delivery.guide",
            "res_id": guide.id,
            "view_mode": "form",
            "target": "current",
        }


class L10nEcDeliveryGuideWizardLine(models.TransientModel):
    _name = "l10n_ec.delivery.guide.wizard.line"
    _description = "Línea del Wizard de Guía de Remisión"

    wizard_id = fields.Many2one("l10n_ec.delivery.guide.wizard", required=True)
    move_line_id = fields.Many2one("stock.move.line")
    move_id = fields.Many2one("stock.move")
    lot_id = fields.Many2one(
        related="move_line_id.lot_id", string="Lote/Serie", readonly=True
    )
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    quantity = fields.Float(string="Cantidad a Incluir", required=True)
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida")
