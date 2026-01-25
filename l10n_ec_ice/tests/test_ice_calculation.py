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
        cls.ice_alcohol = cls.IceCategory.create(
            {
                "code": "3031",
                "name": "Alcohol ICE",
                "type": "specific_content",  # Rate per Liter Pure Alcohol
                "specific_rate": 10.30,
            }
        )

        cls.ice_plastic = cls.IceCategory.create(
            {
                "code": "3680",
                "name": "Plastic Bags",
                "type": "specific",  # Rate per Unit
                "specific_rate": 0.08,
            }
        )

        cls.ice_perfume = cls.IceCategory.create(
            {
                "code": "3072",
                "name": "Perfumes",
                "type": "ad_valorem",  # % of Price
                "ad_valorem_rate": 20.0,
            }
        )

        # 2. Setup Taxes linked to ICE Categories
        cls.tax_ice_alcohol = cls.Tax.create(
            {
                "name": "ICE Alcohol 3031",
                "amount_type": "code",  # Hack to force using compute override
                "l10n_ec_ice_category_id": cls.ice_alcohol.id,
                "amount": 0,  # Controlled by logic
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
