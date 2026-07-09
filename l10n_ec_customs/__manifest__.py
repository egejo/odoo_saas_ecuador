# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Customs (Imports/Exports)",
    "version": "18.0.1.0.0",
    "category": "Operations/Customs",
    "summary": "DAU, Tariff Codes, FODINFA, Import IVA",
    "description": """
Ecuadorian Customs Localization
===============================

Complete customs management for Ecuador (SENAE):

* Declaración Aduanera Única (DAU)
* Tariff Headings (Partidas Arancelarias / HS Codes)
* Import Tax Calculations:
  - Ad Valorem (0-40% based on tariff)
  - FODINFA (0.5% on CIF)
  - IVA Import (15% on CIF + duties)
  - ISD (5% on payments abroad)
* ECUAPASS integration support
* Customs regime tracking

**Regulatory Compliance**: SENAE 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Bug real de empaquetado corregido: este modulo redeclaraba claves de
`ir.config_parameter` (l10n_ec.fodinfa, l10n_ec.customs_iva) ya
registradas por `l10n_ec_base` con el mismo valor pero violando la
constraint de unicidad, bloqueando la instalacion. Corregido. Aparte
de eso: "ECUAPASS integration support" de arriba es una afirmacion sin
ningun codigo real detras (ni un stub) -- no hay ninguna mencion a
ECUAPASS en todo el modulo fuera de este texto. DAU, partidas
arancelarias y el calculo de Ad Valorem/FODINFA/ISD siguen SIN probar
con una importacion real.
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: bug de empaquetado corregido, sin auditar funcionalmente todavía)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": ["stock", "account", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_ec_customs_data.xml",
        "views/l10n_ec_customs_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
}
