# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "l10n_ec_ice")
class TestIceVehicleBracket(TransactionCase):
    """
    Regression test for a real bug found 2026-07-10: this catalog modeled
    "Vehiculos Motorizados" as a single flat 15% ad valorem category
    (code 3092) since day one -- both wrong in structure (the SRI's real
    Tabla 18 tariff for motor vehicles is tiered by PVP/sale-price
    bracket, 5% to 35%, not a flat rate) and in the SRI code itself (3092
    is officially "Servicios de Television Prepagada", unrelated to
    vehicles at all). Replaced with the real PVP-tiered categories.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.IceCategory = cls.env["l10n_ec.ice.category"]

    def test_fake_3092_category_removed(self):
        self.assertFalse(self.IceCategory.search([("code", "=", "3092")]))

    def test_general_bracket_low(self):
        bracket = self.IceCategory.get_vehicle_bracket(15000, is_pickup_or_rescue=False)
        self.assertEqual(bracket.code, "3073")
        self.assertEqual(bracket.ad_valorem_rate, 5.0)

    def test_general_bracket_20k_boundary_inclusive(self):
        """PVP == 20000 must still fall in the "hasta 20000" bracket."""
        bracket = self.IceCategory.get_vehicle_bracket(20000, is_pickup_or_rescue=False)
        self.assertEqual(bracket.code, "3073")

    def test_general_bracket_20k_to_30k(self):
        bracket = self.IceCategory.get_vehicle_bracket(25000, is_pickup_or_rescue=False)
        self.assertEqual(bracket.code, "3686")
        self.assertEqual(bracket.ad_valorem_rate, 10.0)

    def test_pickup_rescue_preferential_bracket(self):
        """A pickup/rescue vehicle at the same $25,000 PVP gets the
        preferential 5% bracket instead of the general 10% one."""
        bracket = self.IceCategory.get_vehicle_bracket(25000, is_pickup_or_rescue=True)
        self.assertEqual(bracket.code, "3684")
        self.assertEqual(bracket.ad_valorem_rate, 5.0)

    def test_pickup_rescue_falls_back_to_general_above_30k(self):
        """The pickup/rescue preferential bracket only covers up to
        $30,000 PVP -- above that, even a pickup truck uses the same
        general schedule as any other vehicle."""
        bracket = self.IceCategory.get_vehicle_bracket(35000, is_pickup_or_rescue=True)
        self.assertEqual(bracket.code, "3075")
        self.assertEqual(bracket.ad_valorem_rate, 15.0)

    def test_general_bracket_40k_to_50k(self):
        bracket = self.IceCategory.get_vehicle_bracket(45000, is_pickup_or_rescue=False)
        self.assertEqual(bracket.code, "3077")
        self.assertEqual(bracket.ad_valorem_rate, 20.0)

    def test_general_bracket_50k_to_60k(self):
        bracket = self.IceCategory.get_vehicle_bracket(55000, is_pickup_or_rescue=False)
        self.assertEqual(bracket.code, "3078")
        self.assertEqual(bracket.ad_valorem_rate, 25.0)

    def test_general_bracket_60k_to_70k(self):
        bracket = self.IceCategory.get_vehicle_bracket(65000, is_pickup_or_rescue=False)
        self.assertEqual(bracket.code, "3079")
        self.assertEqual(bracket.ad_valorem_rate, 30.0)

    def test_general_bracket_above_70k_no_upper_bound(self):
        bracket = self.IceCategory.get_vehicle_bracket(150000, is_pickup_or_rescue=False)
        self.assertEqual(bracket.code, "3080")
        self.assertEqual(bracket.ad_valorem_rate, 35.0)

    def test_onchange_auto_assigns_bracket_from_pvp(self):
        product = self.env["product.product"].create(
            {"name": "Camioneta Prueba ICE", "list_price": 29000.0}
        )
        product.l10n_ec_pvp = 29000.0
        product.l10n_ec_ice_is_pickup_or_rescue = True
        product.product_tmpl_id._onchange_l10n_ec_ice_vehicle_pvp()
        self.assertEqual(product.l10n_ec_ice_category_id.code, "3684")

    def test_onchange_does_not_override_unrelated_category(self):
        """A product manually assigned to a non-vehicle ICE category
        (e.g. perfumes) must not be silently reclassified just because
        someone later fills in an unrelated PVP field."""
        perfume_category = self.IceCategory.search([("code", "=", "3072")], limit=1)
        product = self.env["product.product"].create(
            {
                "name": "Perfume con PVP casual",
                "list_price": 40.0,
                "l10n_ec_ice_category_id": perfume_category.id,
            }
        )
        product.l10n_ec_pvp = 25000.0
        product.product_tmpl_id._onchange_l10n_ec_ice_vehicle_pvp()
        self.assertEqual(product.l10n_ec_ice_category_id.code, "3072")
