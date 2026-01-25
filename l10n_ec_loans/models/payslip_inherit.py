# -*- coding: utf-8 -*-
from odoo import models, fields, api

class L10nEcPayslip(models.Model):
    _inherit = 'l10n_ec.payslip'

    # Add Loan Deduction Field
    loan_deduction = fields.Float("IESS/Company Loans", compute='_compute_loans', store=True)

    @api.depends('employee_id', 'date_start', 'date_end')
    def _compute_loans(self):
        for rec in self:
            # Find unpaid loan installments due in this period
            installments = self.env['l10n_ec.loan.line'].search([
                ('loan_id.employee_id', '=', rec.employee_id.id),
                ('loan_id.state', '=', 'active'),
                ('is_paid', '=', False),
                ('date_due', '>=', rec.date_start),
                ('date_due', '<=', rec.date_end)
            ])
            total = sum(installments.mapped('amount'))
            rec.loan_deduction = total

    # Override total computation to include loans
    @api.depends('total_income', 'total_benefits_cash', 'iess_personal', 'income_tax', 'advances', 'loan_deduction')
    def _compute_totals(self):
        # We need to call super or re-implement.
        # Since we modified the original logic widely, let's re-implement strictly.
        for rec in self:
             # Re-calc Totals (Copy of original + loan_deduction)
             # Note: This overrides the previous method entirely if we use same @api.depends
             # But since 'loan_deduction' is new, we should just subtract it from net_wage?
             # No, net_wage compute needs to know about it.

             # Re-triggering the base logic is messy if we don't fully override.
             # We will just subtract it here:
             rec.net_wage = (rec.total_income + rec.total_benefits_cash) - \
                            rec.iess_personal - rec.income_tax - rec.advances - rec.loan_deduction

    def action_confirm(self):
        # Mark installments as paid
        for rec in self:
            installments = self.env['l10n_ec.loan.line'].search([
                ('loan_id.employee_id', '=', rec.employee_id.id),
                ('loan_id.state', '=', 'active'),
                ('is_paid', '=', False),
                ('date_due', '>=', rec.date_start),
                ('date_due', '<=', rec.date_end)
            ])
            installments.write({'is_paid': True, 'payslip_id': rec.id})

        return super(L10nEcPayslip, self).action_confirm()

