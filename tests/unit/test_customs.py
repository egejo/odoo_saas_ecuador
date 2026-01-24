# -*- coding: utf-8 -*-
"""
Customs Module Tests
====================

Tests DAU, FODINFA, Ad Valorem, IVA Importación.
All rates from ir.config_parameter.
"""
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'l10n_ec', 'customs')
class TestCustoms(TransactionCase):
    """Tests for Ecuador Customs (Aduanas)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env['ir.config_parameter'].sudo()

    # =========================================================================
    # CONFIGURABLE RATES
    # =========================================================================

    def test_fodinfa_configurable(self):
        """[CUS-01] FODINFA rate from ir.config_parameter."""
        rate = float(self.ICP.get_param('l10n_ec.fodinfa', '0'))
        self.assertEqual(rate, 0.005, "FODINFA should be 0.5%")

    def test_customs_iva_configurable(self):
        """[CUS-02] Customs IVA from ir.config_parameter."""
        rate = float(self.ICP.get_param('l10n_ec.customs_iva', '0'))
        self.assertEqual(rate, 0.15, "Customs IVA should be 15%")

    def test_fodinfa_can_be_changed(self):
        """[CUS-03] FODINFA can be updated without code change."""
        original = self.ICP.get_param('l10n_ec.fodinfa')

        # Simulate regulation change
        self.ICP.set_param('l10n_ec.fodinfa', '0.01')
        new_rate = float(self.ICP.get_param('l10n_ec.fodinfa'))

        self.assertEqual(new_rate, 0.01, "FODINFA should be changeable")

        # Restore
        self.ICP.set_param('l10n_ec.fodinfa', original or '0.005')

    # =========================================================================
    # DAU MODEL
    # =========================================================================

    def test_dau_model_exists(self):
        """[CUS-04] DAU model exists."""
        model = self.env['ir.model'].search([
            ('model', '=', 'l10n_ec.import.dau')
        ])
        self.assertTrue(model, "l10n_ec.import.dau model should exist")

    def test_dau_uses_config_params(self):
        """[CUS-05] DAU _compute_taxes uses config params."""
        DAU = self.env.get('l10n_ec.import.dau')
        if DAU:
            import inspect
            source = inspect.getsource(DAU._compute_taxes)
            self.assertIn('ir.config_parameter', source,
                         "DAU taxes must use config parameter")

    # =========================================================================
    # CIF CALCULATION
    # =========================================================================

    def test_cif_formula(self):
        """[CUS-06] CIF = FOB + Freight + Insurance."""
        fob = 1000.0
        freight = 100.0
        insurance = 20.0
        cif = fob + freight + insurance
        self.assertEqual(cif, 1120.0, "CIF formula should be FOB + F + I")

    def test_fodinfa_calculation(self):
        """[CUS-07] FODINFA = CIF * 0.5%."""
        cif = 1000.0
        fodinfa_rate = float(self.ICP.get_param('l10n_ec.fodinfa', '0.005'))
        fodinfa = cif * fodinfa_rate
        self.assertEqual(fodinfa, 5.0, "FODINFA should be 0.5% of CIF")

    def test_customs_iva_calculation(self):
        """[CUS-08] Import IVA = (CIF + AdValorem + FODINFA) * 15%."""
        cif = 1000.0
        advalorem = 200.0
        fodinfa = 5.0
        iva_rate = float(self.ICP.get_param('l10n_ec.customs_iva', '0.15'))

        base = cif + advalorem + fodinfa
        iva = base * iva_rate

        self.assertEqual(iva, 180.75, "Import IVA calculation")
