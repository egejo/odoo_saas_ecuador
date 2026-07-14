# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # SRI 2026: Rebaja Tributaria Inputs
    l10n_ec_family_loads = fields.Integer(
        "Cargas Familiares (SRI - Rebaja Renta)",
        default=0,
        help="Number of legal dependents for Tax Rebate (LORTI Art. 10). "
        "OJO: esta definicion incluye padres/madres dependientes y es "
        "distinta de la que usa Utilidades (ver l10n_ec_utilidades_family_loads) "
        "-- no usar este campo para calcular el 5% de Utilidades.",
    )
    l10n_ec_catastrophic_disease = fields.Boolean(
        "Catastrophic/Rare Disease",
        default=False,
        help="Check if employee or dependent has a certified catastrophic disease (Max Rebate 20 Baskets).",
    )

    # Codigo de Trabajo Art. 97: Cargas Familiares para Utilidades (5%).
    # Definicion legal distinta de la de arriba: solo conyuge/conviviente en
    # union libre e hijos menores de 18 anos o con discapacidad de cualquier
    # edad -- NO incluye padres/madres dependientes (que si cuentan para la
    # rebaja de renta de LORTI). Campo separado a proposito para no repetir
    # el bug encontrado 2026-07-14 (un solo campo mezclando ambas
    # definiciones podia sobre-pagar el 5% de Utilidades).
    l10n_ec_utilidades_family_loads = fields.Integer(
        "Cargas Familiares (Utilidades - Art. 97)",
        default=0,
        help="Conyuge/conviviente en union libre + hijos menores de 18 anos "
        "o con discapacidad de cualquier edad. NO incluye padres/madres "
        "dependientes (Codigo de Trabajo Art. 97, distinto de la rebaja de "
        "impuesto a la renta de LORTI Art. 10).",
    )
