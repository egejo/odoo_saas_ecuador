# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador SRI Electronic Invoicing",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations/SRI",
    "summary": "Full SRI Electronic Invoicing Compliance (2025-2026)",
    "description": """
Ecuador SRI Integration Module
==============================

Complete SRI (Servicio de Rentas Internas) integration:

* SOAP Web Services (RecepcionComprobantesOffline, AutorizacionComprobantesOffline)
* Test and Production environments
* Certificate management (.p12)
* Error handling and retry logic
* Authorization status tracking
* RIDE report generation

**Endpoints**:
- Test: celcer.sri.gob.ec
- Production: cel.sri.gob.ec

**Regulatory Compliance**: SRI 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Este es el modulo con mas trabajo de correccion de todo el fork (19
commits). Al recibirlo, Nota de Credito no estaba implementada en
absoluto (siempre renderizaba el XML de factura sin importar el tipo
de documento -- la primera NC real habria chocado contra la factura
original en el SRI). Se implemento Nota de Credito y Nota de Debito
desde cero, se corrigio el desglose de impuestos y el tipo de
identificacion del comprador, se rediseno el RIDE completo (bordes,
forma de pago, informacion adicional, envio por correo con XML+PDF
segun Art. 6 Res. NAC-DGERCGC18-00000233), y se agrego la leyenda de
regimen RIMPE. Factura, NC y ND confirmadas AUTORIZADO end-to-end
contra el SRI real (ambiente de pruebas). Guia de Remision se
implemento aparte, en el modulo l10n_ec_delivery_guide (tambien
AUTORIZADO end-to-end).

2026-07-10: corregidos 2 bugs reales mas al integrar ICE de verdad por
primera vez (l10n_ec_ice nunca habia calculado nada hasta ese mismo
dia -- ver ese modulo): _get_line_taxes() calculaba el 'valor' de
CUALQUIER impuesto de linea como "base * tarifa / 100", formula valida
solo para amount_type='percent' (IVA, ICE ad valorem) -- para ICE
amount_type='fixed' (especifico/especifico con contenido, un valor en
dolares por unidad, no un porcentaje) esto daba un valor casi cero.
Ademas, _map_tax_codes() no tenia ninguna entrada Tabla 18
(codigoPorcentaje) para ICE -- el codigoPorcentaje real de ICE no es
un codigo generico como IVA, es el mismo codigo por
categoria/producto (3011, 3031, 3680, ...) que ya usa
l10n_ec_ice_category_id.code (Tabla 18 del SRI, "TARIFA DEL ICE") --
por eso ahora depende tambien de l10n_ec_ice. Ninguno de los dos bugs
se habia detectado antes porque ningun impuesto ICE real habia llegado
nunca a este codigo. Ambos corregidos y cubiertos por
tests/test_ice_xml_integration.py; sin probar todavia contra el SRI
real con un producto ICE en una factura.
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: Nota de Credito/Debito implementadas desde cero, RIDE rediseñado, verificado AUTORIZADO contra SRI real)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        "mail",
        "portal",
        "l10n_ec_base",
        "l10n_ec_edi",  # Base EDI module with field definitions
        "l10n_ec_ice",  # account.tax.l10n_ec_ice_category_id, needed to
                        # build the real codigoPorcentaje (Tabla 18) for
                        # any ICE tax -- see _map_tax_codes.
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/report_paperformat.xml",
        "views/account_move_views.xml",
        "views/account_move_xml_template.xml",
        "report/report_invoice.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # Future: Add status badges styling if needed
        ],
    },
    "external_dependencies": {
        "python": ["zeep", "cryptography", "lxml"],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
