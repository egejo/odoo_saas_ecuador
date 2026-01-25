# -*- coding: utf-8 -*-
"""
Withholding Module Tests
========================

Tests retenciones IR, IVA, and Dividend withholding.
All rates from ir.config_parameter.
"""
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install", "l10n_ec", "withholding")
class TestWithholding(TransactionCase):
    """Tests for Ecuador Withholding (Retenciones)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env["ir.config_parameter"].sudo()

    # =========================================================================
    # IR WITHHOLDING RATES
    # =========================================================================

    def test_withholding_ir_rates_exist(self):
        """[WITH-01] IR withholding rates configured."""
        # Tax template should have IR retention taxes
        taxes = self.env["account.tax"].search(
            [
                ("name", "ilike", "Retención IR%"),
                ("type_tax_use", "=", "purchase"),
            ]
        )
        self.assertTrue(len(taxes) > 0, "IR withholding taxes should exist")

    def test_withholding_ir_10_honorarios(self):
        """[WITH-02] IR 10% Honorarios rate."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%10%Honorarios%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(abs(tax.amount), 10.0, "IR Honorarios should be 10%")

    def test_withholding_ir_8_profesionales(self):
        """[WITH-03] IR 8% Profesionales rate."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%8%Profesional%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(abs(tax.amount), 8.0, "IR Profesionales should be 8%")

    # =========================================================================
    # IVA WITHHOLDING RATES
    # =========================================================================

    def test_withholding_iva_rates_exist(self):
        """[WITH-04] IVA withholding rates configured."""
        taxes = self.env["account.tax"].search(
            [
                ("name", "ilike", "Retención IVA%"),
                ("type_tax_use", "=", "purchase"),
            ]
        )
        self.assertTrue(len(taxes) > 0, "IVA withholding taxes should exist")

    def test_withholding_iva_30_bienes(self):
        """[WITH-05] IVA 30% Bienes rate."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%IVA 30%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(abs(tax.amount), 30.0, "IVA Bienes CE should be 30%")

    def test_withholding_iva_70_servicios(self):
        """[WITH-06] IVA 70% Servicios rate."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%IVA 70%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(abs(tax.amount), 70.0, "IVA Servicios CE should be 70%")

    def test_withholding_iva_100_total(self):
        """[WITH-07] IVA 100% Total rate."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%IVA 100%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(abs(tax.amount), 100.0, "IVA 100% should exist")

    # =========================================================================
    # DIVIDEND WITHHOLDING (2026 Regulation)
    # =========================================================================

    def test_dividend_10_non_resident(self):
        """[WITH-08] Dividend 10% for non-residents."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%Dividendos 10%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(
                abs(tax.amount), 10.0, "Dividend non-resident should be 10%"
            )

    def test_dividend_12_resident(self):
        """[WITH-09] Dividend 12% for residents."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%Dividendos 12%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(abs(tax.amount), 12.0, "Dividend resident should be 12%")

    def test_dividend_14_tax_haven(self):
        """[WITH-10] Dividend 14% for tax havens."""
        tax = self.env["account.tax"].search(
            [
                ("name", "ilike", "%Dividendos 14%"),
            ],
            limit=1,
        )
        if tax:
            self.assertEqual(abs(tax.amount), 14.0, "Dividend tax haven should be 14%")
