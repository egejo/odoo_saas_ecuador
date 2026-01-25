# -*- coding: utf-8 -*-
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # SRI 2026: Rebaja Tributaria Inputs
    l10n_ec_family_loads = fields.Integer(
        "Cargas Familiares (SRI)",
        default=0,
        help="Number of legal dependents for Tax Rebate (LORTI Art. 10)."
    )
    l10n_ec_catastrophic_disease = fields.Boolean(
        "Catastrophic/Rare Disease",
        default=False,
        help="Check if employee or dependent has a certified catastrophic disease (Max Rebate 20 Baskets)."
    )
