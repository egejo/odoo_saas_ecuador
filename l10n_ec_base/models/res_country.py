# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCountry(models.Model):
    _inherit = "res.country"

    # Tabla de Codificación de Países del SRI, usada en comprobantes
    # electrónicos (ej. retenciones a proveedores del exterior, ver
    # l10n_ec_withholding) y en el ATS (l10n_ec_reports). Sin este
    # catálogo, cada módulo tenía que pedir el código a mano por
    # proveedor en vez de derivarlo del país ya seleccionado.
    l10n_ec_code_ats = fields.Char(
        string="Código País SRI (ATS)",
        size=3,
        help="Código de país de la Tabla de Codificación de Países del "
        "SRI, usado en comprobantes electrónicos y en el ATS.",
    )
    l10n_ec_code_tax_haven = fields.Char(
        string="Código Paraíso Fiscal SRI",
        size=3,
        help="Código de paraíso fiscal del SRI para el ATS, cuando este "
        "país está catalogado como tal. Vacío si no aplica.",
    )
