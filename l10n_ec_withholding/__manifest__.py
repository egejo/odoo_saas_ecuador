# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Withholding Management (Retenciones)",
    "version": "18.0.1.4.0",
    "category": "Accounting/Localizations",
    "summary": "Vendor Bill Withholding, SRI Authorization, Cancellation Deadline",
    "description": """
Ecuador Withholding Module (Retenciones)
========================================

Complete withholding management for Ecuador:

* Retention document (Comprobante de Retención)
* Income Tax withholdings (IR codes 303, 304, 312, 319, 322, 332, 343, 343A, 343B, 3440, 344A — audited against NAC-DGERCGC26-00000009)
* IVA withholdings (codes 1, 2, 3, 7, 8, 9, 10, 11 — SRI Tabla 20, one per retention percentage)
* ISD withholding (Impuesto a la Salida de Divisas, code 4580)
* Cancellation deadline: day 7 of the month following emission (the old 5-day rule was eliminated by Res. NAC-DGERCGC25-00000017, effective 2026)
* SRI electronic transmission
* XML generation and XAdES signing

**Regulatory Compliance**: SRI 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Al recibir este modulo existian TRES implementaciones de retencion en
paralelo, incompatibles entre si, y ninguna funcionaba: el wizard de
creacion fallaba siempre porque `tax_type` usaba vocabularios
distintos ("1"/"2"/"6" vs "renta"/"iva"/"isd") entre modelos
relacionados, dejando el dominio del campo requerido `tax_id` sin
resultados posibles. Se consolido todo en un unico modelo funcional
(`account.retention`), se reescribio el XML contra el schema real
(faltaba el envoltorio obligatorio docsSustento/docSustento), y se
agrego `action_check_sri` (no existia forma de confirmar AUTORIZADO).
El catalogo completo de codigos (renta/IVA/ISD) fue auditado codigo
por codigo contra la Resolucion NAC-DGERCGC26-00000009 y la Ficha
Tecnica oficial del SRI: varios codigos reales estaban equivocados
desde el dia 1 (ej. 312 con 1.75% cuando el SRI exige 2%; el tipo ISD
no tenia ni un solo codigo cargado, imposible crear una retencion ISD
en la practica). Los 9 codigos de renta y los 7 de IVA quedaron
confirmados AUTORIZADO contra el SRI real, uno por uno. La retencion a
proveedor RIMPE ahora sugiere el codigo correcto automaticamente
(ver l10n_ec_rimpe). La retencion a proveedor genuinamente extranjero
esta implementada (tipoSujetoRetenido) pero no probada contra el SRI
real con un caso real.
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: modelo de retenciones reescrito de 3 implementaciones rotas a 1 funcional, catálogo completo auditado y AUTORIZADO contra SRI real)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "l10n_ec_base",
        "l10n_ec_edi",
        "l10n_ec_sri",
        "account",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_ec_withholding.xml",
        "data/retention_codes_2026.xml",
        "data/retention_template.xml",
        "report/report_retention.xml",
        "views/account_retention_views.xml",
        "views/res_partner_views.xml",
        "wizard/retention_wizard_views.xml",
        "views/account_move_views_fixed.xml",
        "data/mail_template_retention.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
