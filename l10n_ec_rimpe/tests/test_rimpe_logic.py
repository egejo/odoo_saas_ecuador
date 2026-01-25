# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install', 'l10n_ec_rimpe')
class TestRimpeLogic(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Move = cls.env['account.move']

        cls.partner_popular = cls.Partner.create({
            'name': 'Tienda Popular',
            'l10n_ec_rimpe_type': 'popular_business'
        })

        cls.partner_entrepreneur = cls.Partner.create({
            'name': 'Startup Ecuador',
            'l10n_ec_rimpe_type': 'entrepreneur'
        })

        cls.partner_none = cls.Partner.create({
            'name': 'Empresa Grande',
            'l10n_ec_rimpe_type': 'none'
        })

    def test_rimpe_retention_codes(self):
        """Test correct retention codes based on partner type"""
        # Hack: calling _get_rimpe_retention_code on an empty recordset or new instance
        # In reality, this would be used during move creation/posting
        move = self.Move.new({})

        code_pop = move._get_rimpe_retention_code(self.partner_popular)
        self.assertEqual(code_pop, '332B', "Popular Business must calculate 332B (0%)")

        code_ent = move._get_rimpe_retention_code(self.partner_entrepreneur)
        self.assertEqual(code_ent, '343A', "Entrepreneur must calculate 343A (1%)")

        code_none = move._get_rimpe_retention_code(self.partner_none)
        self.assertIsNone(code_none, "General Regime should return None")
