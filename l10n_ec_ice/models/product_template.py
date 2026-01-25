# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_ec_ice_category_id = fields.Many2one(
        'l10n_ec.ice.category',
        string='ICE Category',
        help="SRI Category for ICE tax calculation"
    )

    # Fields required for specific ICE calculations
    l10n_ec_ice_unit_content = fields.Float(
        'ICE Content Unit',
        help="Used for Alcohol (degrees) or Sugar (grams/100g) or Capacity (Liters)",
        default=1.0
    )

    l10n_ec_pvp = fields.Float(
        'PVP (ICE Base)',
        help="Precio de Venta al Publico suggested. Used as base for some Ad Valorem calculations."
    )
