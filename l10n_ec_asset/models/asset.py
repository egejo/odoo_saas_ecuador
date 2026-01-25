# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# LORTI Art. 28 num. 6 - Depreciación activos fijos

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class Asset(models.Model):
    """
    Asset - Activo Fijo

    Legal basis:
    - LORTI Art. 28 num. 6: Depreciación activos fijos
    - SRI tablas de depreciación
    """

    _name = "l10n_ec.asset"
    _description = "Activo Fijo"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "acquisition_date desc"

    name = fields.Char(string="Nombre", required=True, tracking=True)
    code = fields.Char(string="Código", copy=False)
    active = fields.Boolean(default=True)

    # Category
    category_id = fields.Many2one(
        "l10n_ec.asset.category", string="Categoría", required=True, tracking=True
    )

    # Values
    acquisition_value = fields.Monetary(
        string="Valor de Adquisición",
        currency_field="currency_id",
        required=True,
        tracking=True,
    )
    residual_value = fields.Monetary(
        string="Valor Residual", currency_field="currency_id", default=0.0
    )
    depreciated_value = fields.Monetary(
        string="Depreciación Acumulada",
        currency_field="currency_id",
        compute="_compute_depreciation",
        store=True,
    )
    book_value = fields.Monetary(
        string="Valor en Libros",
        currency_field="currency_id",
        compute="_compute_depreciation",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
    )

    # Dates
    acquisition_date = fields.Date(
        string="Fecha Adquisición", required=True, default=fields.Date.today
    )
    start_depreciation_date = fields.Date(
        string="Inicio Depreciación", required=True, default=fields.Date.today
    )

    # Depreciation from category
    depreciation_method = fields.Selection(
        related="category_id.depreciation_method", store=True
    )
    annual_rate = fields.Float(related="category_id.annual_rate", store=True)
    useful_life_years = fields.Integer(
        related="category_id.useful_life_years", store=True
    )

    # State
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("open", "En Uso"),
            ("close", "Cerrado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )

    # Related
    partner_id = fields.Many2one("res.partner", string="Proveedor")
    invoice_id = fields.Many2one("account.move", string="Factura de Compra")
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Cuenta Analítica"
    )

    # Depreciation lines
    depreciation_line_ids = fields.One2many(
        "l10n_ec.asset.depreciation.line", "asset_id", string="Líneas de Depreciación"
    )

    @api.depends("acquisition_value", "residual_value", "depreciation_line_ids.amount")
    def _compute_depreciation(self):
        for asset in self:
            posted_lines = asset.depreciation_line_ids.filtered(lambda l: l.move_posted)
            asset.depreciated_value = sum(posted_lines.mapped("amount"))
            asset.book_value = asset.acquisition_value - asset.depreciated_value

    def action_confirm(self):
        """Confirm asset and generate depreciation schedule."""
        for asset in self:
            asset._generate_depreciation_schedule()
            asset.state = "open"

    def action_close(self):
        """Close asset."""
        self.write({"state": "close"})

    def _generate_depreciation_schedule(self):
        """Generate monthly depreciation lines per LORTI Art. 28."""
        self.ensure_one()

        if not self.useful_life_years or not self.annual_rate:
            raise ValidationError(
                _("La categoría debe tener tasa de depreciación definida.")
            )

        # Delete existing unposted lines
        self.depreciation_line_ids.filtered(lambda l: not l.move_posted).unlink()

        depreciable_value = self.acquisition_value - self.residual_value
        monthly_amount = depreciable_value * (self.annual_rate / 100) / 12
        total_months = self.useful_life_years * 12

        current_date = self.start_depreciation_date
        remaining = depreciable_value

        lines = []
        for i in range(total_months):
            if remaining <= 0:
                break

            amount = min(monthly_amount, remaining)
            remaining -= amount

            lines.append(
                {
                    "asset_id": self.id,
                    "name": _("Depreciación %s/%s") % (i + 1, total_months),
                    "date": current_date,
                    "amount": amount,
                    "depreciated_value": depreciable_value - remaining,
                    "remaining_value": remaining + self.residual_value,
                }
            )

            current_date = current_date + relativedelta(months=1)

        self.env["l10n_ec.asset.depreciation.line"].create(lines)


class AssetDepreciationLine(models.Model):
    """Depreciation Line - Línea de Depreciación"""

    _name = "l10n_ec.asset.depreciation.line"
    _description = "Línea de Depreciación"
    _order = "date"

    asset_id = fields.Many2one("l10n_ec.asset", required=True, ondelete="cascade")
    name = fields.Char(string="Descripción", required=True)
    date = fields.Date(string="Fecha", required=True)
    amount = fields.Monetary(string="Monto", currency_field="currency_id")
    depreciated_value = fields.Monetary(
        string="Depreciación Acumulada", currency_field="currency_id"
    )
    remaining_value = fields.Monetary(
        string="Valor Residual", currency_field="currency_id"
    )
    currency_id = fields.Many2one(related="asset_id.currency_id")

    move_id = fields.Many2one("account.move", string="Asiento Contable")
    move_posted = fields.Boolean(
        string="Contabilizado", compute="_compute_move_posted", store=True
    )

    @api.depends("move_id.state")
    def _compute_move_posted(self):
        for line in self:
            line.move_posted = line.move_id.state == "posted" if line.move_id else False

    def action_create_move(self):
        """Create accounting entry for depreciation."""
        for line in self:
            if line.move_id:
                continue

            asset = line.asset_id
            category = asset.category_id

            if not category.depreciation_account_id or not category.expense_account_id:
                raise ValidationError(
                    _(
                        "La categoría '%s' debe tener cuentas de depreciación configuradas."
                    )
                    % category.name
                )

            move_vals = {
                "date": line.date,
                "journal_id": category.journal_id.id,
                "ref": _("Depreciación %s") % asset.name,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": category.expense_account_id.id,
                            "name": line.name,
                            "debit": line.amount,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": category.depreciation_account_id.id,
                            "name": line.name,
                            "debit": 0,
                            "credit": line.amount,
                        },
                    ),
                ],
            }

            move = self.env["account.move"].create(move_vals)
            line.move_id = move
