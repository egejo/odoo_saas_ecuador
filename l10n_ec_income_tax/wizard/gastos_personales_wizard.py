# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class L10nEcGastosPersonalesWizard(models.TransientModel):
    _name = "l10n_ec.gastos.personales.wizard"
    _description = "Formulario GP: Proyección Gastos Personales"

    def _default_employee(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, default=_default_employee
    )
    year = fields.Integer(
        "Fiscal Year", required=True, default=lambda self: datetime.now().year
    )

    # Expense Categories (LORTI Art. 10)
    housing = fields.Float(
        "Vivienda", help="Rental checks, mortgage interest, property tax, utilities"
    )
    health = fields.Float(
        "Salud", help="Medical fees, medication, insurance, deductibles"
    )
    education = fields.Float(
        "Educación / Arte / Cultura", help="Tuition, supplies, art/culture classes"
    )
    food = fields.Float("Alimentación", help="Groceries, restaurants")
    clothing = fields.Float("Vestimenta", help="Clothing and footwear")
    tourism = fields.Float("Turismo Nacional", help="Registered local tourism expenses")

    total_projected = fields.Float(
        "Total Expenses", compute="_compute_total", store=True
    )

    @api.depends("housing", "health", "education", "food", "clothing", "tourism")
    def _compute_total(self):
        for rec in self:
            rec.total_projected = (
                rec.housing
                + rec.health
                + rec.education
                + rec.food
                + rec.clothing
                + rec.tourism
            )

    def action_apply_to_contract(self):
        self.ensure_one()
        # Find active contract for the employee
        contract = self.env["hr.contract"].search(
            [("employee_id", "=", self.employee_id.id), ("state", "=", "open")], limit=1
        )

        if not contract:
            raise UserError(
                _("No active contract found for %s. Cannot update projected expenses.")
                % self.employee_id.name
            )

        # Update the field on the contract
        contract.write({"l10n_ec_projected_expenses": self.total_projected})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Projected expenses updated on contract ($%s)")
                % self.total_projected,
                "type": "success",
                "sticky": False,
            },
        }
