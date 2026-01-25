# -*- coding: utf-8 -*-
from odoo import models, fields, api


class L10nEcTaxTable(models.Model):
    _name = "l10n_ec.tax.table"
    _description = "Impuesto a la Renta Progressive Table (2026)"
    _order = "basic_fraction asc"

    year = fields.Integer("Fiscal Year", required=True, default=2026)
    basic_fraction = fields.Float("Basic Fraction", required=True)
    excess_until = fields.Float("Excess Until", required=True)
    basic_tax = fields.Float("Basic Tax on Fraction", required=True)
    marginal_rate = fields.Float("Marginal Rate %", required=True)

    @api.model
    def get_tax_for_base(self, taxable_base, year=2026):
        """
        Calculates Impuesto Causado based on the progressive table.
        """
        row = self.search(
            [
                ("year", "=", year),
                ("basic_fraction", "<=", taxable_base),
                ("excess_until", ">=", taxable_base),
            ],
            limit=1,
        )

        # Handle the last bracket (Infinity)
        if not row:
            row = self.search(
                [("year", "=", year), ("basic_fraction", "<=", taxable_base)],
                order="basic_fraction desc",
                limit=1,
            )

        if not row:
            return 0.0

        # Formula: Basic Tax + ((Base - Basic Fraction) * Marginal Rate)
        excess_amount = taxable_base - row.basic_fraction
        tax_on_excess = excess_amount * (row.marginal_rate / 100)
        return row.basic_tax + tax_on_excess


class L10nEcFamilyBasket(models.Model):
    _name = "l10n_ec.family.basket"
    _description = "Canasta Básica Familiar & Rebaja Criteria (LORTI Art. 10)"

    year = fields.Integer("Fiscal Year", required=True, default=2026)
    basket_cost = fields.Float(
        "Cost of Canasta Básica (Jan)",
        required=True,
        help="Value of CBA in January of the fiscal year",
    )

    # Validation Rules (Resolution NAC-DGERCGC25-00000043)
    # Rebate = Min(ProjectedExpenses, (N_Baskets * BasketCost)) * 18%

    @api.model
    def calculate_rebate(
        self, projected_expenses, family_loads, catastrophic_disease=False, year=2026
    ):
        """
        Calculates the 'Rebaja Tributaria' (Tax Credit).
        LORTI Rule: 18% of the lesser of (Projected Expenses) OR (N * Canastas).
        """
        config = self.search([("year", "=", year)], limit=1)
        if not config:
            # Fallback safehouse or raise?
            # Vibe Rule #1: No fake defaults. If no config, we can't calc.
            return 0.0

        # Determine N (Number of Baskets) based on Loads or Disease
        if catastrophic_disease:
            n_baskets = 20.0  # Max limit immediately
        else:
            if family_loads == 0:
                n_baskets = 7.0
            elif family_loads == 1:
                n_baskets = 9.0
            elif family_loads == 2:
                n_baskets = 11.0
            elif family_loads == 3:
                n_baskets = 14.0
            elif family_loads == 4:
                n_baskets = 17.0
            else:
                n_baskets = 20.0

        max_deductible_base = n_baskets * config.basket_cost

        # Comparison
        applicable_base = min(projected_expenses, max_deductible_base)

        # Rebate is 18% of that base
        return applicable_base * 0.18
