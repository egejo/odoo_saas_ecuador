# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Base Localization (NEC 2026)",
    "version": "18.0.1.1.0",
    "category": "Accounting/Localizations",
    "summary": "Chart of Accounts, Tax Templates, and Identity Validation (SRI 2026)",
    "description": """
Ecuador Base Localization Module
================================

This module provides the base localization for Ecuador:

* Chart of Accounts (Plan de Cuentas NEC)
* Tax Templates (IVA 15%, 5%, 0%)
* RUC/Cédula validation (Módulo 11, Módulo 10)
* Document Types for SRI
* Ecuador-specific company fields

**Regulatory Compliance**: SRI 2026, Resolution NAC-DGERCGC25-00000017
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        "purchase",
        "purchase_stock",
        "l10n_latam_invoice_document",
        # l10n_ec (localizacion oficial de Odoo para Ecuador) ya estaba
        # instalado en este servidor (arrastrado por el plan de cuentas
        # elegido al configurar la compañía) pero nunca se declaro aqui
        # como dependencia real, pese a que este modulo reutiliza sus
        # catalogos (l10n_latam.document.type, l10n_ec.sri.payment, etc.)
        # y varios metodos de res.partner (_l10n_ec_get_identification_type).
        "l10n_ec",
    ],
    "data": [
        "security/l10n_ec_groups.xml",
        "security/ir.model.access.csv",
        "data/l10n_ec_sri_config.xml",
        "data/l10n_ec_config_data.xml",
        "data/l10n_ec_catalogs_data.xml",
        "data/l10n_ec_provinces.xml",
        "data/l10n_ec.canton.csv",
        "data/account_chart_template.xml",
        "data/res.country.csv",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/res_country_views.xml",
    ],
    "demo": [],  # Demo data is wizard-controlled, not auto-loaded
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
