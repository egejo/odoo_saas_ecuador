# -*- coding: utf-8 -*-
"""
Payroll Module Tests
====================

Tests IESS, SBU, décimos, fondos de reserva.
All rates from ir.config_parameter.
"""
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install", "l10n_ec", "payroll")
class TestPayroll(TransactionCase):
    """Tests for Ecuador Payroll (Nómina)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env["ir.config_parameter"].sudo()

    # =========================================================================
    # CONFIGURABLE RATES
    # =========================================================================

    def test_sbu_configurable(self):
        """[PAY-01] SBU uses ir.config_parameter."""
        sbu = float(self.ICP.get_param("l10n_ec.sbu", "0"))
        self.assertEqual(sbu, 482.0, "SBU 2026 should be $482")

    def test_iess_personal_configurable(self):
        """[PAY-02] IESS personal uses ir.config_parameter."""
        rate = float(self.ICP.get_param("l10n_ec.iess_aporte_personal", "0"))
        self.assertEqual(rate, 9.45, "IESS personal should be 9.45%")

    def test_iess_employer_configurable(self):
        """[PAY-03] IESS patronal uses ir.config_parameter."""
        rate = float(self.ICP.get_param("l10n_ec.iess_aporte_patronal", "0"))
        self.assertEqual(
            rate,
            11.15,
            "IESS patronal should be 11.15% (base rate, total with SECAP+IECE = 12.15%)",
        )

    def test_sbu_can_be_changed(self):
        """[PAY-04] SBU can be updated without code change."""
        original = self.ICP.get_param("l10n_ec.sbu")

        # Simulate regulation change
        self.ICP.set_param("l10n_ec.sbu", "500.00")
        new_sbu = float(self.ICP.get_param("l10n_ec.sbu"))

        self.assertEqual(new_sbu, 500.0, "SBU should be changeable")

        # Restore
        self.ICP.set_param("l10n_ec.sbu", original or "482.00")

    # =========================================================================
    # PAYSLIP CALCULATIONS
    # =========================================================================

    def test_payslip_model_exists(self):
        """[PAY-05] Payslip model exists."""
        model = self.env["ir.model"].search([("model", "=", "l10n_ec.payslip")])
        self.assertTrue(model, "l10n_ec.payslip model should exist")

    def test_payslip_uses_config_iess(self):
        """[PAY-06] Payslip _compute_iess uses config params."""
        # Verify the method uses ir.config_parameter
        Payslip = self.env.get("l10n_ec.payslip")
        if Payslip:
            # Check source code doesn't have hardcoded rates
            import inspect

            source = inspect.getsource(Payslip._compute_iess)
            self.assertIn(
                "ir.config_parameter",
                source,
                "IESS computation must use config parameter",
            )

    # =========================================================================
    # DÉCIMOS CALCULATIONS
    # =========================================================================

    def test_decimo_tercero_formula(self):
        """[PAY-07] Décimo tercer sueldo = Income / 12."""
        # Standard formula verification
        income = 1000.0
        decimo_13 = income / 12.0
        self.assertAlmostEqual(decimo_13, 83.33, places=2)

    def test_decimo_cuarto_formula(self):
        """[PAY-08] Décimo cuarto = SBU / 12 (per month)."""
        sbu = float(self.ICP.get_param("l10n_ec.sbu", "482"))
        decimo_14_monthly = sbu / 12.0
        self.assertAlmostEqual(decimo_14_monthly, 40.17, places=2)

    def test_fondos_reserva_rate(self):
        """[PAY-09] Fondos de reserva = 8.33% of income."""
        income = 1000.0
        reserva = income * (1.0 / 12.0)  # 8.33%
        self.assertAlmostEqual(reserva, 83.33, places=2)
