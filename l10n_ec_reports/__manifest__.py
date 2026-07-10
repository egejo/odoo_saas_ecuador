# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Reports (ATS, Form 104)",
    "version": "18.0.1.1.0",
    "category": "Accounting/Localizations/Reporting",
    "summary": "ATS (Anexo Transaccional Simplificado) XML Generation",
    "description": """
Ecuador Tax Reports Module
==========================

SRI Tax reporting for Ecuador:

* ATS (Anexo Transaccional Simplificado)
  - Sales summary
  - Purchases summary
  - Withholdings summary
  - Cancelled documents
  - XML generation for upload to SRI
* Form 104 support (IVA declaration)

**Filing Deadlines**: Monthly, by RUC 9th digit

**Regulatory Compliance**: SRI 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Auditado y reescrito 2026-07-10 contra la Ficha Tecnica oficial del ATS
del SRI y contra Enterprise l10n_ec_reports_ats (solo como referencia
estructural, nunca copiado -- y con la advertencia de que el propio
Enterprise puede estar desactualizado frente a normativa reciente).
Antes de esta sesion, el wizard nunca se habia ejecutado ni una sola
vez: generar el XML crasheaba de inmediato (campo inexistente
`l10n_ec_authorization`, y la plantilla de Form 103/104 referenciaba un
campo `l10n_ec_entity` en res.company que tampoco existe). Bugs reales
corregidos, todos confirmados generando el XML/PDF real contra datos de
produccion (julio 2026):
* Bloque AIR (retenciones de renta) nunca aparecia: comparaba
  tax_type == "1" contra un campo cuyo vocabulario real es
  "renta"/"iva"/"isd".
* Notas de Credito/Debito (compras y ventas) invisibles en el ATS: el
  dominio de busqueda solo incluia in_invoice/out_invoice, nunca
  in_refund/out_refund.
* Campos obligatorios ausentes del XML: parteRel (compras y ventas),
  tipoEm (F/E), y el desglose completo de retencion de IVA por tarifa
  (valRetBien10/20/30/50/70/100 -- antes solo se reportaba renta).
* Ventas: factura (01)/nota de venta (02) deben reportarse con el
  codigo generico 18 en el ATS (Tabla 4), no con su propio codigo.
* Notas de Credito/Debito sin el bloque docModificado/estabModificado/
  etc. que las enlaza al comprobante original (Tabla 4).
* Talon resumen (ventasEstablecimiento/totalVentas): solo debe sumar
  ventas de emision FISICA, nunca electronica (el detalle electronico
  ya viaja en el XML autorizado de cada comprobante) -- antes sumaba
  todo. Con Adrenasports 100% electronico, el valor correcto hoy es
  0.00.
* Clasificacion de IVA/ICE por linea: antes comparaba el nombre
  traducible del grupo de impuesto contra literales en ingles
  ("ICE"/"IVA"), fragil e incorrecto en un entorno es_EC -- ahora usa
  account.tax.group.l10n_ec_type (catalogo real del modulo CORE
  l10n_ec, confirmado poblado correctamente en produccion).
* Catalogo Tabla 5 (Sustento Tributario) de l10n_ec_edi tenia 3 de 7
  etiquetas equivocadas (mismo patron de codigos SRI mal etiquetados ya
  visto en retenciones/ICE); corregido y completado a los 13 codigos
  reales.
* Formulario 103/104 (PDF): referenciaba una variable `company` que el
  motor de reportes de Odoo no inyecta para wizards sin doc propio --
  crasheaba al generar el PDF real (no solo el HTML).
Form 104 sigue siendo un borrador de ayuda para declarar manualmente en
el portal del SRI (no hay submission electronica de IVA), consistente
con el cambio normativo de 2026 que exige pagar junto con declarar pero
no cambia la estructura del formulario. Limitacion conocida: no hay
fuente de datos para retenciones que CLIENTES le hacen a Adrenasports
(valorRetIva/valorRetRenta en ventas quedan en 0.00).
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: ATS/Form103/104 auditado y corregido 2026-07-10)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "l10n_ec_base",
        "l10n_ec_edi",
        "l10n_ec_withholding",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ats_template.xml",
        "report/form_templates.xml",
        "report/reports.xml",
        "wizard/l10n_ec_ats_wizard_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
