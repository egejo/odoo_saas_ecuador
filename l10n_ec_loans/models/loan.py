# -*- coding: utf-8 -*-
from odoo import models, fields


class L10nEcLoan(models.Model):
    _name = "l10n_ec.loan"
    _description = "Employee Loan (IESS / Company)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Description", required=True)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    loan_type = fields.Selection(
        [
            ("iess_qui", "IESS Quirografario"),
            ("iess_hip", "IESS Hipotecario"),
            ("company", "Company Advance/Loan"),
        ],
        string="Type",
        required=True,
        default="company",
    )

    amount_total = fields.Float("Total Amount", required=True)
    date_start = fields.Date("Start Date", required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("paid", "Paid"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )

    installment_ids = fields.One2many(
        "l10n_ec.loan.line", "loan_id", string="Installments"
    )

    def action_activate(self):
        self.write({"state": "active"})


class L10nEcLoanLine(models.Model):
    _name = "l10n_ec.loan.line"
    _description = "Loan Installment"

    loan_id = fields.Many2one("l10n_ec.loan", required=True, ondelete="cascade")
    date_due = fields.Date("Due Date", required=True)
    amount = fields.Float("Amount", required=True)
    is_paid = fields.Boolean("Paid", default=False)
    payslip_id = fields.Many2one("l10n_ec.payslip", string="Deduced in Payslip")
