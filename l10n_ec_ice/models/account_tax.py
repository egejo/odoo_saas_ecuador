# -*- coding: utf-8 -*-
from odoo import api, models, fields


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_ec_ice_category_id = fields.Many2one(
        "l10n_ec.ice.category", string="ICE Category (SRI)"
    )

    @api.onchange("l10n_ec_ice_category_id")
    def _onchange_l10n_ec_ice_category_id(self):
        """Keep amount_type/amount in sync with the SRI category so the real
        Odoo 18 tax engine (account.tax._eval_tax_amount_*) computes it
        correctly on its own, without any custom dispatch."""
        for tax in self:
            cat = tax.l10n_ec_ice_category_id
            if not cat:
                continue
            if cat.type == "ad_valorem":
                tax.amount_type = "percent"
                tax.amount = cat.ad_valorem_rate
            else:  # specific or specific_content
                tax.amount_type = "fixed"
                tax.amount = cat.specific_rate

    @api.model_create_multi
    def create(self, vals_list):
        taxes = super().create(vals_list)
        taxes._sync_l10n_ec_ice_amount()
        return taxes

    def write(self, vals):
        res = super().write(vals)
        if "l10n_ec_ice_category_id" in vals:
            self._sync_l10n_ec_ice_amount()
        return res

    def _sync_l10n_ec_ice_amount(self):
        for tax in self:
            cat = tax.l10n_ec_ice_category_id
            if not cat:
                continue
            if cat.type == "ad_valorem":
                tax.amount_type = "percent"
                tax.amount = cat.ad_valorem_rate
            else:
                tax.amount_type = "fixed"
                tax.amount = cat.specific_rate

    def _eval_taxes_computation_prepare_product_fields(self):
        # Odoo core hook: declare which product fields the tax engine must
        # preload into evaluation_context['product'] for this batch of taxes.
        field_names = super()._eval_taxes_computation_prepare_product_fields()
        if any(
            tax.l10n_ec_ice_category_id.type == "specific_content" for tax in self
        ):
            field_names = field_names | {"l10n_ec_ice_unit_content"}
        return field_names

    def _eval_tax_amount_fixed_amount(self, batch, raw_base, evaluation_context):
        # "Specific with content" ICE (alcohol degrees, sugar grams) needs the
        # product-specific content factor on top of the plain fixed amount
        # that core already handles for "specific" (e.g. cigarettes, bags).
        self.ensure_one()
        if self.l10n_ec_ice_category_id.type == "specific_content":
            content = evaluation_context["product"].get(
                "l10n_ec_ice_unit_content", 0.0
            )
            sign = -1 if evaluation_context["price_unit"] < 0.0 else 1
            return sign * evaluation_context["quantity"] * content * self.amount
        return super()._eval_tax_amount_fixed_amount(
            batch, raw_base, evaluation_context
        )
