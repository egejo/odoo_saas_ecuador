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

        --------------------------------------------------------------------
        Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
        --------------------------------------------------------------------
        Hasta 2026-07-09 este modulo no hacia casi nada de lo que decia: no
        existia ningun soporte a nivel de la propia compañia (agregado desde
        cero, ver l10n_ec_edi/l10n_ec_sri: leyenda "CONTRIBUYENTE REGIMEN
        RIMPE" en XML/RIDE), y el helper de codigo de retencion por
        proveedor devolvia "332B"/"343A" desde el dia 1 -- codigos reales de
        OTROS conceptos tributarios (inmuebles / energia electrica), no de
        RIMPE en absoluto -- y nunca estaba conectado a nada (comentario
        original: "Logic to override retention application would go here").
        Corregido a los codigos reales (332/343) y conectado de verdad al
        wizard de retenciones, que ahora sugiere el codigo automaticamente.
        Probado end-to-end contra el SRI real: AUTORIZADO.
    """,
    "author": "Somatech Ecuador, egejo (fork: régimen de compañía implementado desde cero, código de retención corregido de equivocado/muerto a correcto/conectado, AUTORIZADO en SRI real)",
    "depends": ["account", "l10n_ec_base", "l10n_ec_withholding"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
