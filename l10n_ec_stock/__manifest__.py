# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Stock & Logistics (Guía de Remisión)",
    "version": "18.0.1.0.0",
    "category": "Inventory/Localizations",
    "summary": "Guía de Remisión, Transportistas, Motivos de Traslado",
    "description": """
Ecuador Stock & Logistics Module
=================================

Electronic Guía de Remisión (Waybill) for Ecuador:

* Guía de Remisión document (Document Type 06)
* Carrier/Transporter data management
* Transfer reason codes (Venta, Traslado, Exportación, etc.)
* Route information
* XML generation and SRI transmission
* Integration with stock.picking

**Regulatory Compliance**: SRI 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
ADVERTENCIA: este modulo NUNCA se monta en el `addons_path` de la
instalacion de produccion que mantiene este fork -- su nombre tecnico
`l10n_ec_stock` choca directamente con el modulo homonimo OFICIAL de
Odoo Community. Los dos no pueden coexistir. Como resultado, nadie ha
instalado ni probado este modulo ni una sola vez en el contexto de
este fork -- todo lo que dice arriba, incluida la Guia de Remision
completa con "XML generation and SRI transmission", es texto heredado
del repositorio original, nunca verificado aqui. La Guia de Remision
electronica sigue SIN implementar en absoluto en los modulos que este
fork si usa (`l10n_ec_edi`/`l10n_ec_sri`) -- ni XML ni RIDE, tampoco
existe en el modulo oficial de Enterprise.
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "l10n_ec_base",
        "l10n_ec_edi",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/l10n_ec_transport_views.xml",
        "data/l10n_ec_stock_data.xml",
        "data/guia_template.xml",
        "views/stock_picking_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
