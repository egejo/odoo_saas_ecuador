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
contra el SRI real (ambiente de pruebas). Guia de Remision sigue sin
implementar (tampoco existe en el modulo oficial de Enterprise).
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
