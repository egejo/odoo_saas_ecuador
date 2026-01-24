from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    l10n_ec_regime = fields.Selection([
        ('general', 'General'),
        ('construction', 'Construction'),
        ('agriculture', 'Agriculture'),
        ('part_time', 'Part Time'),
    ], string='IESS Regime', default='general', required=True)

    l10n_ec_accumulate_13 = fields.Boolean("Accumulate 13th Salary", default=False)
    l10n_ec_accumulate_14 = fields.Boolean("Accumulate 14th Salary", default=False)
    l10n_ec_accumulate_reserve = fields.Boolean("Accumulate Reserve Funds", default=True)

    # SRI Projections
    l10n_ec_projected_expenses = fields.Float("Projected Personal Expenses (SRI Encuesta)")
