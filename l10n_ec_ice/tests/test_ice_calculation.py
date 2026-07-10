# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "l10n_ec_ice")
class TestICECalculation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.IceCategory = cls.env["l10n_ec.ice.category"]
        cls.Tax = cls.env["account.tax"]
        cls.Product = cls.env["product.product"]
        cls.company = cls.env.user.company_id
        cls.company.country_id = cls.env.ref("base.ec")

        # 1. Setup ICE Categories
        # Codes use a 9xxx test range: the real SRI codes (3031/3680/3072/...)
        # are already loaded from data/l10n_ec.ice.category.csv in any DB
        # where this module is installed, and code has a unique constraint.
        cls.ice_alcohol = cls.IceCategory.create(
            {
                "code": "9031",
                "name": "Alcohol ICE (test)",
                "type": "specific_content",  # Rate per Liter Pure Alcohol
                "specific_rate": 10.30,
            }
        )

        cls.ice_plastic = cls.IceCategory.create(
            {
                "code": "9680",
                "name": "Plastic Bags (test)",
                "type": "specific",  # Rate per Unit
                "specific_rate": 0.08,
            }
        )

        cls.ice_perfume = cls.IceCategory.create(
            {
                "code": "9072",
                "name": "Perfumes (test)",
                "type": "ad_valorem",  # % of Price
                "ad_valorem_rate": 20.0,
            }
        )

        # 2. Setup Taxes linked to ICE Categories
        # amount_type/amount are enforced server-side from the ICE category
        # (see AccountTax._sync_l10n_ec_ice_amount) so the real Odoo 18 tax
        # engine (amount_type in fixed/percent/division, there is no 'code'
        # anymore) computes it without any custom dispatch.
        cls.tax_ice_alcohol = cls.Tax.create(
            {
                "name": "ICE Alcohol 3031",
                "l10n_ec_ice_category_id": cls.ice_alcohol.id,
                "country_id": cls.company.country_id.id,
            }
        )
        cls.tax_ice_plastic = cls.Tax.create(
            {
                "name": "ICE Fundas 3680",
                "l10n_ec_ice_category_id": cls.ice_plastic.id,
                "country_id": cls.company.country_id.id,
            }
        )
        cls.tax_ice_perfume = cls.Tax.create(
            {
                "name": "ICE Perfumes 3072",
                "l10n_ec_ice_category_id": cls.ice_perfume.id,
                "country_id": cls.company.country_id.id,
            }
        )

        # 3. Setup Products
        cls.product_whisky = cls.Product.create(
            {
                "name": "Whisky 750ml 40%",
                "l10n_ec_ice_category_id": cls.ice_alcohol.id,
                "l10n_ec_ice_unit_content": 0.30,  # 0.75L * 0.40% = 0.30 Liters Pure
                "list_price": 50.00,
                "taxes_id": [(6, 0, [cls.tax_ice_alcohol.id])],
            }
        )
        cls.product_bag = cls.Product.create(
            {
                "name": "Funda Plastica",
                "l10n_ec_ice_category_id": cls.ice_plastic.id,
                "list_price": 0.10,
                "taxes_id": [(6, 0, [cls.tax_ice_plastic.id])],
            }
        )
        cls.product_perfume = cls.Product.create(
            {
                "name": "Perfume",
                "l10n_ec_ice_category_id": cls.ice_perfume.id,
                "list_price": 40.00,
                "taxes_id": [(6, 0, [cls.tax_ice_perfume.id])],
            }
        )

    def test_ice_specific_content_alcohol(self):
        """
        Test Alcohol ICE: Qty * Pure Alcohol * Rate
        Qty: 10 bottles
        Content: 0.30 (750ml * 40%)
        Rate: $10.30
        Exp: 10 * 0.30 * 10.30 = $30.90
        """
        taxes = self.tax_ice_alcohol.compute_all(
            price_unit=50.0, quantity=10, product=self.product_whisky
        )
        tax_amount = taxes["taxes"][0]["amount"]
        self.assertAlmostEqual(tax_amount, 30.90, places=2)

    def test_ice_missing_content_default(self):
        """
        Test default behavior if content is 0 or missing (should default to 1 for safety or 0?)
        Current logic defaults to 1.0 from product model default
        """
        product_simple = self.Product.create(
            {
                "name": "Simple Alcohol",
                "l10n_ec_ice_category_id": self.ice_alcohol.id,
                # content defaults to 1.0
            }
        )
        # 1 unit * 1.0 content * 10.30 rate = 10.30
        taxes = self.tax_ice_alcohol.compute_all(
            price_unit=100.0, quantity=1, product=product_simple
        )
        self.assertAlmostEqual(taxes["taxes"][0]["amount"], 10.30, places=2)

    def test_ice_specific_plastic_bags(self):
        """Plain 'specific' ICE needs no override: core 'fixed' amount_type
        already does quantity * amount once synced from the category."""
        self.assertEqual(self.tax_ice_plastic.amount_type, "fixed")
        self.assertAlmostEqual(self.tax_ice_plastic.amount, 0.08, places=4)
        taxes = self.tax_ice_plastic.compute_all(
            price_unit=0.10, quantity=100, product=self.product_bag
        )
        # 100 bags * $0.08 = $8.00
        self.assertAlmostEqual(taxes["taxes"][0]["amount"], 8.00, places=2)

    def test_ice_ad_valorem_perfume(self):
        """Ad valorem ICE needs no override either: core 'percent'
        amount_type already applies the rate to the price base."""
        self.assertEqual(self.tax_ice_perfume.amount_type, "percent")
        self.assertAlmostEqual(self.tax_ice_perfume.amount, 20.0, places=2)
        taxes = self.tax_ice_perfume.compute_all(
            price_unit=40.0, quantity=1, product=self.product_perfume
        )
        # $40 * 20% = $8.00
        self.assertAlmostEqual(taxes["taxes"][0]["amount"], 8.00, places=2)

    def test_ice_category_change_syncs_tax_amount(self):
        """Regression guard for the original bug: this module used to rely
        on amount_type='code' and an overridden _compute_amount, neither of
        which exists in the Odoo 18 tax engine anymore (amount_type is
        limited to group/fixed/percent/division, and taxes are evaluated via
        _eval_tax_amount_fixed_amount/_eval_tax_amount_price_included/
        _eval_tax_amount_price_excluded) -- so the ICE amount was never
        actually computed by any real invoice/order in production."""
        tax = self.Tax.create(
            {
                "name": "ICE Sync Test",
                "country_id": self.company.country_id.id,
            }
        )
        tax.l10n_ec_ice_category_id = self.ice_perfume
        self.assertEqual(tax.amount_type, "percent")
        self.assertAlmostEqual(tax.amount, 20.0, places=2)
