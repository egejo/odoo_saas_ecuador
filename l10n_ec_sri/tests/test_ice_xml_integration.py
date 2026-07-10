# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "l10n_ec_sri")
class TestIceXmlIntegration(TransactionCase):
    """
    Regression test for two real bugs found auditing l10n_ec_ice (2026-07-10):

    1. L10nEcSriXml._get_line_taxes() computed every tax's XML 'valor' as
       "base_imponible * tax.amount / 100", which is only correct for
       amount_type='percent' taxes (IVA, ICE ad valorem). For amount_type=
       'fixed' taxes (ICE specific/specific_content -- a dollar amount per
       unit, not a percentage) this produced a wildly wrong <valor>/<tarifa>
       in the per-line <detalle>/<impuestos> block of the invoice XML, even
       though the header-level <totalConImpuestos> (built from real posted
       account.move.line balances, not this formula) was already correct.

    2. _map_tax_codes() had no Tabla 18 (codigoPorcentaje) entry for ICE at
       all -- _TABLA18_CODIGO_PORCENTAJE only covers IVA rates. Per the
       SRI's own Ficha Tecnica ("TABLA 18: TARIFA DEL ICE"), ICE's
       codigoPorcentaje isn't a small generic code like IVA's: it's the
       *same per-product-group code* (3011 cigarrillos, 3031 alcohol, 3680
       fundas plasticas, ...) already used as l10n_ec.ice.category.code.
       Any invoice with an ICE tax would have raised ValidationError
       immediately, before ever reaching the SRI. (Not even Odoo
       Enterprise's l10n_ec_edi supports this -- its own code comments
       "non-IVA cases such as ICE ... not supported" and would KeyError.)

    Neither was ever caught before because l10n_ec_ice itself never
    calculated anything (see the account_tax.py fix in the same commit),
    so no ICE tax had ever reached either of these code paths on a real
    invoice.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.user.company_id
        cls.company.country_id = cls.env.ref("base.ec")
        cls.SriXml = cls.env["l10n_ec.sri.xml"]

        cls.partner = cls.env["res.partner"].create(
            {"name": "Cliente Prueba ICE XML", "country_id": cls.company.country_id.id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Funda Plastica (test XML)", "list_price": 0.10}
        )

        # The l10n_ec CoA template instantiates its account.tax.group
        # records per-company with a company-id-prefixed xmlid (e.g.
        # "account.1_tax_group_ice"), not a fixed "l10n_ec.tax_group_ice"
        # -- look them up by their real l10n_ec_type instead of guessing
        # the xmlid.
        TaxGroup = cls.env["account.tax.group"]
        tax_group_ice = TaxGroup.search([("l10n_ec_type", "=", "ice")], limit=1)
        tax_group_vat15 = TaxGroup.search([("l10n_ec_type", "=", "vat15")], limit=1)

        # Real SRI category (code 3680, Fundas Plasticas, $0.08/unit) from
        # l10n_ec_ice's own catalog data -- setting it triggers
        # AccountTax._sync_l10n_ec_ice_amount() to derive amount_type/amount
        # automatically, exercising the real integration end-to-end.
        ice_category_fundas = cls.env["l10n_ec.ice.category"].search(
            [("code", "=", "3680")], limit=1
        )
        cls.tax_ice_fixed = cls.env["account.tax"].create(
            {
                "name": "ICE Fundas Test",
                "type_tax_use": "sale",
                "country_id": cls.company.country_id.id,
                "tax_group_id": tax_group_ice.id,
                "l10n_ec_ice_category_id": ice_category_fundas.id,
            }
        )
        cls.tax_iva_percent = cls.env["account.tax"].create(
            {
                "name": "IVA 15% Test",
                "amount_type": "percent",
                "amount": 15.0,
                "type_tax_use": "sale",
                "country_id": cls.company.country_id.id,
                "tax_group_id": tax_group_vat15.id,
            }
        )

        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": "2026-07-10",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "quantity": 100,
                            "price_unit": 0.10,
                            "tax_ids": [
                                (6, 0, [cls.tax_ice_fixed.id, cls.tax_iva_percent.id])
                            ],
                        },
                    )
                ],
            }
        )

    def test_line_taxes_fixed_ice_not_computed_as_percent(self):
        """
        100 units * $0.08/unit ICE = $8.00 -- NOT
        price_subtotal($10.00) * 0.08 / 100 = $0.008 (the old, wrong
        formula treating the fixed $ rate as if it were a percentage).
        Also asserts the Tabla 18 codigoPorcentaje is the real SRI
        category code (3680, Fundas Plasticas), not a KeyError/generic
        code.
        """
        line = self.invoice.invoice_line_ids
        line_taxes = self.SriXml._get_line_taxes(line)
        ice_entry = next(t for t in line_taxes if t["codigo"] == "3")
        self.assertEqual(ice_entry["codigo_porcentaje"], "3680")
        self.assertAlmostEqual(ice_entry["valor"], 8.00, places=2)

    def test_line_taxes_percent_iva_unaffected(self):
        """15% IVA on a $10.00 base must still compute correctly (regression
        guard: fixing the 'fixed' case must not break the 'percent' case)."""
        line = self.invoice.invoice_line_ids
        line_taxes = self.SriXml._get_line_taxes(line)
        iva_entry = next(t for t in line_taxes if t["codigo_porcentaje"] == "4")
        self.assertAlmostEqual(iva_entry["base_imponible"], 10.00, places=2)
        self.assertAlmostEqual(iva_entry["valor"], 1.50, places=2)
