# -*- coding: utf-8 -*-
{
    "name": "Ecuador - RIMPE Regime",
    "version": "1.0",
    "category": "Accounting/Localizations",
    "summary": "Manage RIMPE (Emprendedores & Negocios Populares)",
    "description": """
        Implements LORTI Art. 97 (RIMPE).
        Supports:
        - Partner Classification (Popular vs Entrepreneur)
        - Special Retention Codes (332 Negocio Popular 0%, 343 Emprendedor 1%) suggested automatically when creating a withholding against a RIMPE-classified vendor

        NOTE: "Notas de Venta" (SRI document type 02) is a pre-printed paper document, not part of the electronic invoicing schema, and was dropped from this description (it was listed before but never implementable within this EDI scope).
    """,
    "author": "Somatech Ecuador",
    "depends": ["account", "l10n_ec_base", "l10n_ec_withholding"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
