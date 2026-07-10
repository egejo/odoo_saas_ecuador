# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Electronic Invoicing (SRI 2026)",
    "version": "18.0.1.1.0",
    "category": "Accounting/Localizations",
    "summary": "Electronic Invoicing, XAdES-BES Signing, and SRI Transmission (Ficha 2.32)",
    "description": """
Ecuador Electronic Invoicing Module
===================================

This module provides full SRI electronic invoicing:

* XML Generation (Factura, Nota Crédito, Nota Débito, Guía Remisión)
* XAdES-BES Digital Signature (SHA-256)
* Access Key generation (49 digits, Mod 11)
* SRI SOAP transmission (Test/Production)
* RIDE PDF generation
* Consumidor Final validation ($50 limit, no annulment)
* 7-day annulment rule enforcement

**Ficha Técnica**: Version 2.32
**Regulatory Compliance**: SRI 2026, Resolution NAC-DGERCGC25-00000017

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
La firma XAdES-BES original era criptograficamente invalida (bug de
canonicalizacion c14n al usar namespace por defecto en vez de
prefijos ds:/etsi:) y el certificado .p12 ni siquiera se
deserializaba (bug de tipos str/bytes) -- ninguna factura firmada con
el codigo original habria sido aceptada nunca por el SRI. Ambos
corregidos y verificados con `signxml` contra un certificado real.
Tambien se agrego el regimen tributario de la propia compañia
(l10n_ec_regime, ausente por completo) y se corrigio un bug de zona
horaria que fechaba comprobantes un dia adelante cerca de medianoche
UTC. Guía de Remisión sigue sin implementar pese a estar listada
arriba (tampoco existe en el módulo oficial de Enterprise).
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: firma XAdES-BES corregida de invalida a verificada, regimen RIMPE agregado)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "l10n_ec_base",
        "account_edi",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/l10n_ec_certificate_views.xml",
        "views/res_company_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "external_dependencies": {
        "python": ["zeep", "cryptography", "lxml", "requests"],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
