# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Reports (ATS, Form 104)",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations/Reporting",
    "summary": "ATS (Anexo Transaccional Simplificado) XML Generation",
    "description": """
Ecuador Tax Reports Module
==========================

SRI Tax reporting for Ecuador:

* ATS (Anexo Transaccional Simplificado)
  - Sales summary
  - Purchases summary
  - Withholdings summary
  - Cancelled documents
  - XML generation for upload to SRI
* Form 104 support (IVA declaration)

**Filing Deadlines**: Monthly, by RUC 9th digit

**Regulatory Compliance**: SRI 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Instalado y carga sin error, con traducciones es_EC agregadas -- pero
la generacion real del XML del ATS y el Formulario 104 NO ha sido
probada todavia. Cada modulo de este fork que si se probo de verdad
tuvo al menos un bug real -- no asumir que este funciona correctamente
solo porque instala limpio.
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: instalado y traducido, sin auditar funcionalmente todavía)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "l10n_ec_base",
        "l10n_ec_edi",
        "l10n_ec_withholding",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ats_template.xml",
        "report/form_templates.xml",
        "report/reports.xml",
        "wizard/l10n_ec_ats_wizard_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
