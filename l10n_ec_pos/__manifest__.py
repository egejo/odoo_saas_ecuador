# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Point of Sale (Electronic Invoicing)",
    "version": "18.0.1.0.0",
    "category": "Sales/Point of Sale",
    "summary": "SRI Electronic Invoicing for POS",
    "description": """
Ecuador POS Electronic Invoicing
================================

Al validar el pago, la orden se factura y transmite al SRI de inmediato
(el navegador espera la autorizacion sin bloquear ningun worker de Odoo);
el ticket de rollo impreso incluye los datos obligatorios de una
Representacion Impresa del Documento Electronico (RIDE) en formato
reducido: emisor, receptor, tipo/numero de comprobante, fecha, estado del
SRI, y numero de autorizacion/clave de acceso con su codigo de barras.

**Regulatory Compliance**: SRI 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Reescrito 2026-07-13: la version original de este modulo era decorativa
-- generaba una clave de acceso propia en pos.order.create() pero nunca
la firmaba ni transmitia, y su plantilla de recibo con la clave nunca se
conectaba al ticket real. Ahora la facturacion real usa el mismo
account.move/action_send_sri/action_check_sri ya probado end-to-end
contra el SRI (ver checkpoint de Punto de Venta en CLAUDE.md del repo
principal, 2026-07-12/13), disparado automaticamente al validar el pago.
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: reescrito 2026-07-13, probado end-to-end contra el SRI)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "point_of_sale",
        "l10n_ec_sri",
    ],
    "data": [
        "views/pos_config_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "l10n_ec_pos/static/src/js/**/*",
            "l10n_ec_pos/static/src/xml/**/*",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
