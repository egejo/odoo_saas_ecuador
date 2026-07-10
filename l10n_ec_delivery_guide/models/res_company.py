# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    # A diferencia de account.retention (l10n_ec_withholding), que dejó el
    # prefijo estab/ptoEmi de su secuencia hardcodeado a "001-001-" (gap
    # documentado ahí mismo), aquí se exponen como campos de configuración
    # para no repetir esa limitación en un módulo nuevo.
    l10n_ec_delivery_guide_establishment = fields.Char(
        string="Guía de Remisión: Establecimiento",
        default="001",
        help="Código de establecimiento (3 dígitos) usado en la clave de "
        "acceso y el secuencial de las guías de remisión electrónicas.",
    )
    l10n_ec_delivery_guide_emission_point = fields.Char(
        string="Guía de Remisión: Punto de Emisión",
        default="001",
        help="Código de punto de emisión (3 dígitos) usado en la clave de "
        "acceso y el secuencial de las guías de remisión electrónicas.",
    )
