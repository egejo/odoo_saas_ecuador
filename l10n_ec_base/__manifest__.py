# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Base Localization (NEC 2026)",
    "version": "18.0.1.2.0",
    "category": "Accounting/Localizations",
    "summary": "Chart of Accounts, Tax Templates, and Identity Validation (SRI 2026)",
    "description": """
Ecuador Base Localization Module
================================

This module provides the base localization for Ecuador:

* Chart of Accounts (Plan de Cuentas NEC)
* Tax Templates (IVA 15%, 5%, 0%)
* RUC/Cédula validation (Módulo 11, Módulo 10)
* Document Types for SRI
* Ecuador-specific company fields

**Regulatory Compliance**: SRI 2026, Resolution NAC-DGERCGC25-00000017

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Bug sistemico real encontrado en produccion: este modulo redeclaraba
con sus propios xmlids el mismo catalogo de tipos de documento SRI que
el `l10n_ec` core de Odoo ya provee, sin declarar `l10n_ec` como
dependencia real pese a usarlo -- 7 codigos duplicados dejaban
`l10n_latam_document_type_id` sin asignar de forma ambigua en
comprobantes nuevos, y ese valor vacio colaba el texto literal "False"
en la clave de acceso (`ValueError: invalid literal for int(): 'e'`
en produccion real). Corregido declarando la dependencia real y
eliminando el CSV duplicado. La validacion RUC/Cedula (Modulo 10/11)
ya NO bloquea el guardado si el digito verificador no cuadra -- solo
se registra en el log, mismo criterio que usa el propio `l10n_ec` core
("el SRI ha declarado que esta validacion ya no es obligatoria para
algunos numeros de RUC/cedula"); la validacion de longitud/formato si
sigue bloqueando errores de digitacion inequivocos. Se agrego tambien
el catalogo de paises SRI (`l10n_ec_code_ats`, 241 paises) reutilizado
por `l10n_ec_withholding` para retenciones a proveedores extranjeros.
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: bug real de catálogo duplicado corregido, catálogo de países SRI agregado)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        "purchase",
        "purchase_stock",
        "l10n_latam_invoice_document",
        # l10n_ec (localizacion oficial de Odoo para Ecuador) ya estaba
        # instalado en este servidor (arrastrado por el plan de cuentas
        # elegido al configurar la compañía) pero nunca se declaro aqui
        # como dependencia real, pese a que este modulo reutiliza sus
        # catalogos (l10n_latam.document.type, l10n_ec.sri.payment, etc.)
        # y varios metodos de res.partner (_l10n_ec_get_identification_type).
        "l10n_ec",
    ],
    "data": [
        "security/l10n_ec_groups.xml",
        "security/ir.model.access.csv",
        "data/l10n_ec_sri_config.xml",
        "data/l10n_ec_config_data.xml",
        "data/l10n_ec_catalogs_data.xml",
        "data/l10n_ec_provinces.xml",
        "data/l10n_ec.canton.csv",
        "data/account_chart_template.xml",
        "data/res.country.csv",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/res_country_views.xml",
    ],
    "demo": [],  # Demo data is wizard-controlled, not auto-loaded
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
