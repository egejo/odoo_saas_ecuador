from odoo import models, fields, api
from datetime import date

class L10nEcPayslip(models.Model):
    _name = 'l10n_ec.payslip'
    _description = 'Ecuadorian Payslip'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(readonly=True) # e.g. "Cedula - Month/Year"
    employee_id = fields.Many2one('hr.employee', required=True)
    contract_id = fields.Many2one('hr.contract', required=True)

    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)

    days_worked = fields.Float(default=30.0)

    # Earnings
    wage = fields.Float("Base Wage", compute='_compute_wage', store=True, readonly=False)
    overtime_hours = fields.Float("Overtime (50%) Hours")
    supplementary_hours = fields.Float("Supplementary (100%) Hours")
    commission = fields.Float("Commissions")
    bonus = fields.Float("Bonuses")

    # Computations
    total_income = fields.Float("Total Income", compute='_compute_totals', store=True)

    # Deductions
    iess_personal = fields.Float("IESS Personal (9.45%)", compute='_compute_iess', store=True)
    income_tax = fields.Float("Impuesto Renta", default=0.0)
    advances = fields.Float("Salary Advances")

    # Employer Costs
    iess_employer = fields.Float("IESS Patronal (12.15%)", compute='_compute_iess', store=True)

    # Benefits (Provisions)
    thirteenth = fields.Float("13th Salary", compute='_compute_benefits', store=True)
    fourteenth = fields.Float("14th Salary", compute='_compute_benefits', store=True)
    reserve_funds = fields.Float("Reserve Funds", compute='_compute_benefits', store=True)

    net_wage = fields.Float("Net Wage", compute='_compute_totals', store=True)
    total_benefits_cash = fields.Float("Benefits (Cash)", compute='_compute_benefits', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Verification'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft', tracking=True)

    @api.depends('contract_id')
    def _compute_wage(self):
        for rec in self:
            rec.wage = rec.contract_id.wage if rec.contract_id else 0.0

    @api.depends('wage', 'overtime_hours', 'supplementary_hours', 'commission', 'bonus')
    def _compute_totals(self):
        for rec in self:
            # Simple calc for now - assumes Wage is monthly
            ot_rate = (rec.wage / 240) * 1.5
            supp_rate = (rec.wage / 240) * 2.0

            ot_pay = rec.overtime_hours * ot_rate
            supp_pay = rec.supplementary_hours * supp_rate

            rec.total_income = rec.wage + ot_pay + supp_pay + rec.commission + rec.bonus
            rec.net_wage = (rec.total_income + rec.total_benefits_cash) - rec.iess_personal - rec.income_tax - rec.advances

    @api.depends('total_income')
    def _compute_iess(self):
        """
        Calculate IESS contributions using configurable rates.
        Rates from ir.config_parameter for easy regulatory updates.
        """
        ICP = self.env['ir.config_parameter'].sudo()

        # Get IESS rates from config (configurable, not hardcoded)
        iess_personal_rate = float(ICP.get_param('l10n_ec.iess_aporte_personal', '9.45')) / 100
        iess_employer_rate = float(ICP.get_param('l10n_ec.iess_aporte_patronal', '12.15')) / 100

        for rec in self:
            # IESS Personal contribution
            rec.iess_personal = rec.total_income * iess_personal_rate
            # IESS Employer contribution
            rec.iess_employer = rec.total_income * iess_employer_rate

    @api.depends('total_income', 'contract_id.l10n_ec_accumulate_13', 'contract_id.l10n_ec_accumulate_14', 'contract_id.l10n_ec_accumulate_reserve')
    def _compute_benefits(self):
        # Fetch SBU from Config Parameter, default to 482.0 (2026 value per Acuerdo MDT-2025-195)
        sbu_param = self.env['ir.config_parameter'].sudo().get_param('l10n_ec.sbu', '482.0')
        try:
            sbu = float(sbu_param)
        except ValueError:
            sbu = 482.0  # SBU 2026

        for rec in self:
            # 13th: Total Income / 12
            rec.thirteenth = rec.total_income / 12.0

            # 14th: SBU / 12 (if worked full month)
            # Logic: SBU / 360 * days_worked (standard 30-day month)
            rec.fourteenth = (sbu / 360.0) * rec.days_worked

            # Reserve Funds: 8.3333...% of Total Income (usually after 1 year)
            # 1 / 12 = 0.083333...
            rec.reserve_funds = rec.total_income * (1.0 / 12.0)

            # Determine Cash Payout (Mensualizado) vs Accumulation (Provision only)
            cash_total = 0.0
            contract = rec.contract_id

            # If NOT accumulating, pay it now
            if contract and not contract.l10n_ec_accumulate_13:
                cash_total += rec.thirteenth

            if contract and not contract.l10n_ec_accumulate_14:
                cash_total += rec.fourteenth

            if contract and not contract.l10n_ec_accumulate_reserve:
                cash_total += rec.reserve_funds

            rec.total_benefits_cash = cash_total

    def action_confirm(self):
        self.write({'state': 'done'})

    @api.model
    def create(self, vals):
        res = super(L10nEcPayslip, self).create(vals)
        res.name = f"{res.employee_id.name} - {res.date_start}"
        return res
