# -*- coding: utf-8 -*-
from odoo import models, fields, api


class L10nEcDeliveryGuideLine(models.Model):
    _name = "l10n_ec.delivery.guide.line"
    _description = "Línea de Guía de Remisión"

    delivery_guide_id = fields.Many2one(
        "l10n_ec.delivery.guide",
        string="Guía de Remisión",
        required=True,
        ondelete="cascade",
        index=True,
    )
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    quantity = fields.Float(string="Cantidad", required=True)
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida")

    # Lotes/series realmente usados para ESTA linea de ESTA guia (una
    # linea de guia puede representar solo una parte de lo movido en el
    # picking si el usuario reparte la carga en varias guias -- ver
    # l10n_ec_delivery_guide.py). Es la base del anexo de numeros de
    # serie: el Reglamento de Comprobantes de Venta, Retencion y
    # Documentos Complementarios (Art. 19 num. 2) exige consignar el
    # numero de serie cuando el bien esta identificado de esa forma, no
    # es solo una mejora de UX.
    move_line_ids = fields.Many2many(
        "stock.move.line", string="Movimientos de Stock (lotes/series)"
    )
    lot_names = fields.Char(
        string="Números de Serie/Lote", compute="_compute_lot_names", store=True
    )

    @api.depends("move_line_ids.lot_id.name", "move_line_ids.lot_name")
    def _compute_lot_names(self):
        for line in self:
            names = set(filter(None, line.move_line_ids.mapped("lot_id.name")))
            names |= set(filter(None, line.move_line_ids.mapped("lot_name")))
            line.lot_names = ", ".join(sorted(names))
