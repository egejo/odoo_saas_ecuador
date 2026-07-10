# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_ec_ice_category_id = fields.Many2one(
        "l10n_ec.ice.category",
        string="ICE Category",
        help="SRI Category for ICE tax calculation",
    )

    # Fields required for specific ICE calculations
    l10n_ec_ice_unit_content = fields.Float(
        "ICE Content Unit",
        help="Used for Alcohol (degrees) or Sugar (grams/100g) or Capacity (Liters)",
        default=1.0,
    )

    l10n_ec_pvp = fields.Float(
        "PVP (ICE Base)",
        help="Precio de Venta al Publico suggested. Used as base for some Ad Valorem calculations.",
    )

    l10n_ec_ice_is_pickup_or_rescue = fields.Boolean(
        "Camioneta o Vehiculo de Rescate (ICE)",
        help="Solo aplica a Vehiculos Motorizados: si esta marcado, el "
        "vehiculo usa el tramo preferencial de ICE para camionetas y "
        "vehiculos de rescate (Tabla 18 del SRI), valido solo hasta "
        "USD 30.000 de PVP -- por encima de ese monto se usa el tramo "
        "general igual que cualquier otro vehiculo.",
    )

    @api.onchange("l10n_ec_pvp", "l10n_ec_ice_is_pickup_or_rescue")
    def _onchange_l10n_ec_ice_vehicle_pvp(self):
        """
        Auto-sugiere el tramo de ICE (Tabla 18 del SRI) segun el PVP real
        del vehiculo, en vez de dejar que el usuario adivine cual de los
        ~7 codigos de tramo aplica. Solo actua si la categoria ya
        seleccionada es vacia o es ella misma un tramo de vehiculo -- para
        no pisar una categoria no relacionada con vehiculos que el
        usuario haya elegido a proposito para este producto.
        """
        for product in self:
            current = product.l10n_ec_ice_category_id
            if current and not current.vehicle_subtype:
                continue
            if not product.l10n_ec_pvp:
                continue
            bracket = self.env["l10n_ec.ice.category"].get_vehicle_bracket(
                product.l10n_ec_pvp, product.l10n_ec_ice_is_pickup_or_rescue
            )
            if bracket:
                product.l10n_ec_ice_category_id = bracket.id
