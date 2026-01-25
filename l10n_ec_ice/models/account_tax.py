# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_ec_ice_category_id = fields.Many2one('l10n_ec.ice.category', string='ICE Category (SRI)')

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        """
        Override Tax Computation for Ecuador ICE.
        Handles Specific (Quantity-based) and Ad Valorem (Price-based).
        """
        self.ensure_one()

        # Standard Odoo Tax behavior if no ICE Category
        if not self.l10n_ec_ice_category_id or self.country_id.code != 'EC':
            return super()._compute_amount(base_amount, price_unit, quantity, product, partner)

        ice_cat = self.l10n_ec_ice_category_id

        # 1. Ad Valorem: % of Price (Standard Odoo behavior works, just uses rate)
        if ice_cat.type == 'ad_valorem':
            return base_amount * (ice_cat.ad_valorem_rate / 100)

        # 2. Specific: Fixed Amount per Unit
        if ice_cat.type == 'specific':
            # Quantity * Rate
            return quantity * ice_cat.specific_rate

        # 3. Specific with Content (Alcohol/Sugar)
        if ice_cat.type == 'specific_content':
            # Quantity * Content_Factor * Rate
            # Content factor comes from product (defaults to 1.0)
            content = product.l10n_ec_ice_unit_content if product else 1.0
            return quantity * content * ice_cat.specific_rate

        return 0.0
