# -*- coding: utf-8 -*-
{
    "name": "Ecuador - ICE (Impuesto Consumos Especiales)",
    "version": "1.0",
    "category": "Accounting/Localizations",
    "summary": "Manage specific and ad valorem ICE taxes",
    "description": """
        Implements LORTI Title III (Art. 75-89) for ICE.
        Supports:
        - Specific Rates (e.g. Cigarettes, Bags)
        - Specific Rates with Content (Alcohol, Sugar)
        - Ad Valorem Rates (Perfumes, Vehicles)

        --------------------------------------------------------------------
        Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
        --------------------------------------------------------------------
        Instalado y carga sin error, con traducciones es_EC agregadas --
        pero NO auditado ni probado con un producto real todavia. Cada
        modulo de este fork que si se probo de verdad tuvo al menos un
        bug real -- no asumir que este funciona correctamente solo porque
        instala limpio.
    """,
    "author": "Somatech Ecuador, egejo (fork: instalado y traducido, sin auditar funcionalmente todavía)",
    "depends": ["account", "l10n_ec_base", "product"],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_ec.ice.category.csv",
        "views/l10n_ec_ice_category_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
