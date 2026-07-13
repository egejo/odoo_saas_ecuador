# -*- coding: utf-8 -*-
from odoo import models, fields, api


class L10nEcPayslip(models.Model):
    _inherit = "l10n_ec.payslip"

    # Add Loan Deduction Field
    loan_deduction = fields.Float(
        "IESS/Company Loans", compute="_compute_loans", store=True
    )

    # Redeclarar el compute de net_wage (no _compute_totals: ese nombre ya
    # esta ocupado por l10n_ec_hr_payroll y computa ademas total_income/
    # income_tax -- redefinirlo aqui con el mismo nombre lo reemplazaba por
    # completo (misma resolucion de metodo de Python, ultimo modulo cargado
    # gana), dejando total_income/income_tax sin calcular NUNCA. Bug real
    # encontrado 2026-07-13 probando el primer payslip real.
    net_wage = fields.Float(
        "Net Wage", compute="_compute_net_wage_with_loans", store=True
    )

    @api.depends("employee_id", "date_start", "date_end")
    def _compute_loans(self):
        for rec in self:
            # Find unpaid loan installments due in this period
            installments = self.env["l10n_ec.loan.line"].search(
                [
                    ("loan_id.employee_id", "=", rec.employee_id.id),
                    ("loan_id.state", "=", "active"),
                    ("is_paid", "=", False),
                    ("date_due", ">=", rec.date_start),
                    ("date_due", "<=", rec.date_end),
                ]
            )
            total = sum(installments.mapped("amount"))
            rec.loan_deduction = total

    @api.depends(
        "total_income",
        "total_benefits_cash",
        "iess_personal",
        "income_tax",
        "advances",
        "loan_deduction",
    )
    def _compute_net_wage_with_loans(self):
        for rec in self:
            rec.net_wage = (
                (rec.total_income + rec.total_benefits_cash)
                - rec.iess_personal
                - rec.income_tax
                - rec.advances
                - rec.loan_deduction
            )

    def action_confirm(self):
        # Mark installments as paid
        for rec in self:
            installments = self.env["l10n_ec.loan.line"].search(
                [
                    ("loan_id.employee_id", "=", rec.employee_id.id),
                    ("loan_id.state", "=", "active"),
                    ("is_paid", "=", False),
                    ("date_due", ">=", rec.date_start),
                    ("date_due", "<=", rec.date_end),
                ]
            )
            installments.write({"is_paid": True, "payslip_id": rec.id})

        return super(L10nEcPayslip, self).action_confirm()
