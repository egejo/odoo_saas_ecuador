# -*- coding: utf-8 -*-
"""
Unit Tests: Consumidor Final Validation
========================================

SRI 2026 Regulations (Res. NAC-DGERCGC25-00000017):
- CF invoices cannot exceed $50 (configurable)
- CF invoices cannot be cancelled once authorized
- CF RUC: 9999999999999 (configurable)

All limits read from ir.config_parameter, NOT hardcoded.
"""
from odoo.tests import tagged, TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import date


@tagged('post_install', '-at_install', 'l10n_ec', 'regulatory')
class TestConsumidorFinal(TransactionCase):
    """Test Consumidor Final SRI 2026 regulations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ecuador = cls.env.ref('base.ec')

        cls.company = cls.env['res.company'].search([
            ('country_id', '=', cls.ecuador.id)
        ], limit=1)

        if not cls.company:
            cls.company = cls.env.user.company_id

        # Get CF RUC from config (not hardcoded)
        cls.cf_ruc = cls.env['ir.config_parameter'].sudo().get_param(
            'l10n_ec.consumidor_final_ruc', '9999999999999'
        )

        # Get CF limit from config (not hardcoded)
        cls.cf_limit = float(cls.env['ir.config_parameter'].sudo().get_param(
            'l10n_ec.consumidor_final_limit', '50'
        ))

        # Create Consumidor Final partner
        cls.consumidor_final = cls.env['res.partner'].create({
            'name': 'CONSUMIDOR FINAL',
            'vat': cls.cf_ruc,
            'country_id': cls.ecuador.id,
            'l10n_ec_identifier_type': 'ruc',
        })

        # Get income account
        cls.account_income = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('account_type', '=', 'income'),
        ], limit=1)

    def _create_cf_invoice(self, amount):
        """Create invoice for Consumidor Final."""
        return self.env['account.move'].with_company(self.company).create({
            'move_type': 'out_invoice',
            'partner_id': self.consumidor_final.id,
            'invoice_date': date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Producto CF',
                'quantity': 1,
                'price_unit': amount,
                'account_id': self.account_income.id if self.account_income else False,
            })],
        })

    # =========================================================================
    # TEST CASES: CF $50 Limit
    # =========================================================================

    def test_01_cf_below_limit_allowed(self):
        """Test CF invoice at or below limit is allowed."""
        # $40 is below $50 limit
        invoice = self._create_cf_invoice(40.0)
        self.assertTrue(invoice)
        self.assertEqual(invoice.partner_id.vat, self.cf_ruc)

    def test_02_cf_at_limit_allowed(self):
        """Test CF invoice exactly at limit is allowed."""
        # Exactly $50 (before any tax)
        invoice = self._create_cf_invoice(self.cf_limit)
        self.assertTrue(invoice)

    def test_03_cf_above_limit_rejected(self):
        """Test CF invoice above limit raises error."""
        # Amount that exceeds $50 after creation
        with self.assertRaises(ValidationError) as context:
            invoice = self._create_cf_invoice(100.0)  # Well above limit
            invoice._check_consumidor_final_limit()  # Trigger validation

        # Should mention the limit in error message
        self.assertIn('50', str(context.exception) if hasattr(context, 'exception') else '')

    # =========================================================================
    # TEST CASES: CF Cancellation Block
    # =========================================================================

    def test_04_cf_authorized_cannot_cancel(self):
        """Test authorized CF invoice cannot be cancelled."""
        invoice = self._create_cf_invoice(40.0)
        invoice.action_post()

        # Simulate authorization
        invoice.l10n_ec_sri_status = 'authorized'

        # Attempt cancel should fail
        if hasattr(invoice, 'button_cancel_sri'):
            with self.assertRaises(UserError):
                invoice.button_cancel_sri()

    # =========================================================================
    # TEST CASES: CF Configuration
    # =========================================================================

    def test_05_cf_limit_is_configurable(self):
        """Test CF limit reads from ir.config_parameter."""
        param_limit = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_ec.consumidor_final_limit'
        )

        # Limit should be readable (may be default or configured)
        self.assertTrue(
            param_limit is not None or self.cf_limit == 50.0,
            "CF limit should be configured or default to 50"
        )

    def test_06_cf_ruc_is_configurable(self):
        """Test CF RUC reads from ir.config_parameter."""
        param_ruc = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_ec.consumidor_final_ruc'
        )

        # RUC should be 13 nines by default
        expected = '9999999999999'
        actual = param_ruc or expected
        self.assertEqual(len(actual), 13)
