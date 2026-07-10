# -*- coding: utf-8 -*-
from odoo import models, fields, api


class L10nEcIceCategory(models.Model):
    _name = "l10n_ec.ice.category"
    _description = "ICE Tax Category (SRI)"
    _rec_name = "name"

    code = fields.Char("SRI Code", size=4, required=True, help="Codigo SRI (Tabla 6)")
    name = fields.Char("Description", required=True)

    type = fields.Selection(
        [
            ("specific", "Specific Rate (Amount per Unit)"),
            ("specific_content", "Specific Rate with Content (Alcohol, Sugar)"),
            ("ad_valorem", "Ad Valorem (Percentage of Price)"),
        ],
        string="ICE Type",
        required=True,
        default="ad_valorem",
    )

    # For Specific Rates
    specific_rate = fields.Float(
        "Specific Rate ($)", digits=(12, 4), help="Dollar amount per unit/liter/gram"
    )

    # For Ad Valorem Rates
    ad_valorem_rate = fields.Float("Ad Valorem Rate (%)", digits=(12, 2))

    active = fields.Boolean(default=True)

    # Vehiculos Motorizados (Tabla 18 del SRI): el ICE ad valorem no es un
    # porcentaje unico por categoria -- varia por tramo de PVP (Precio de
    # Venta al Publico). Cada tramo real es su propia categoria/tax (mismo
    # patron que cualquier otro codigo de este catalogo, ver
    # get_vehicle_bracket para como se selecciona el tramo correcto segun
    # el PVP del vehiculo). Estos 2 campos solo aplican a categorias tipo
    # "vehicle_general"/"vehicle_pickup_rescue"; para el resto quedan en 0.
    vehicle_subtype = fields.Selection(
        [
            ("general", "Vehiculos en general"),
            ("pickup_rescue", "Camionetas y Vehiculos de Rescate"),
        ],
        string="Tramo de Vehiculo (SRI)",
        help="Si esta categoria es un tramo de ICE de Vehiculos "
        "Motorizados (Tabla 18), a que tipo de vehiculo aplica. Los "
        "tramos 'Camionetas y Vehiculos de Rescate' solo cubren hasta "
        "los USD 30.000 de PVP; por encima de ese monto se usa el tramo "
        "general correspondiente.",
    )
    pvp_min = fields.Float(
        "PVP Minimo (exclusivo)",
        help="El tramo aplica si el PVP del vehiculo es mayor a este "
        "valor (0 = sin minimo, incluye el primer tramo).",
    )
    pvp_max = fields.Float(
        "PVP Maximo (inclusivo)",
        help="El tramo aplica si el PVP del vehiculo es menor o igual a "
        "este valor (0 = sin maximo, tramo mas alto).",
    )

    _sql_constraints = [("code_uniq", "unique(code)", "The SRI Code must be unique!")]

    @api.model
    def get_vehicle_bracket(self, pvp, is_pickup_or_rescue=False):
        """
        Resuelve la categoria ICE (tramo de PVP, Tabla 18 del SRI) que
        corresponde a un vehiculo dado su PVP real -- reemplaza el codigo
        unico "Vehiculos Motorizados 15% plano" que este catalogo tenia
        desde el dia 1 (y que ademas usaba el codigo SRI equivocado, 3092,
        que en realidad corresponde a "Servicios de Television
        Prepagada"). Camionetas/rescate tienen un tramo preferencial
        propio solo hasta USD 30.000 de PVP; por encima de ese monto (o
        si el vehiculo no es camioneta/rescate) se usa el tramo general.
        """
        candidates = self.search([("vehicle_subtype", "!=", False)], order="pvp_min")
        subtypes = ["pickup_rescue", "general"] if is_pickup_or_rescue else ["general"]
        for subtype in subtypes:
            for cat in candidates.filtered(lambda c: c.vehicle_subtype == subtype):
                if pvp > cat.pvp_min or cat.pvp_min == 0.0:
                    if cat.pvp_max == 0.0 or pvp <= cat.pvp_max:
                        return cat
        return self.browse()
