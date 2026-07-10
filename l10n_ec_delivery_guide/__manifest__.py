# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 egejo
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Guía de Remisión Electrónica",
    "version": "18.0.1.0.0",
    "category": "Inventory/Localizations",
    "summary": "Guía de Remisión (codDoc 06): transportista, XML, firma y transmisión SRI",
    "description": """
Guía de Remisión Electrónica (Ecuador)
=======================================

Último de los 5 comprobantes electrónicos del SRI que faltaba en este fork
(factura, nota de crédito, nota de débito y comprobante de retención ya
estaban probados AUTORIZADO contra el SRI real). Implementado desde cero
en 2026-07-10 -- ni Enterprise `l10n_ec_edi` ni este fork tenían ninguna
implementación real (ver más abajo el estado del intento previo).

* Documento `l10n_ec.delivery.guide`, independiente de `stock.picking`
  (relación N:1, no 1:1): permite emitir varias guías desde un mismo
  despacho de bodega o transferencia interna (ej. dos camiones, dos
  viajes), y emitir incluso después de que el despacho ya fue validado.
* Transportista (`l10n_ec.driver`) y vehículo (`l10n_ec.vehicle`).
* Anexo de números de serie/lote por línea (XML + RIDE) -- no es solo
  una mejora de UX: el Reglamento de Comprobantes de Venta, Retención y
  Documentos Complementarios (Art. 19 núm. 2) exige consignar el número
  de serie cuando el bien está identificado de esa forma.
* XML contra el esquema real v1.1.0 de la Ficha Técnica oficial del SRI
  (`guiaRemision`, codDoc 06), firma XAdES-BES y transmisión SOAP
  reutilizando la infraestructura de `l10n_ec_edi`.
* RIDE con el mismo layout de bordes que factura/NC/ND/retención.

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
El upstream de somatechlat traía un módulo `l10n_ec_stock` con un intento
de esto (modelo sobre `stock.picking` directamente, transportista,
plantilla XML), pero su nombre técnico choca con el módulo homónimo
OFICIAL de Odoo Community -- los dos no pueden coexistir en el mismo
`addons_path`, así que nunca se instaló ni se probó ni una sola vez en
este fork. Revisado a fondo antes de reemplazarlo: tenía bugs reales
(mismo patrón que todo lo demás en este fork la primera vez que se
revisa con cuidado) -- `rucTransportista` tomaba el número de licencia
de conducir del chofer en vez de su RUC/cédula real; `motivoTraslado`
enviaba el código interno de selección ("traslado") en vez de un texto
legible; faltaba por completo el bloque `docSustento` (referencia a la
factura de venta que motiva el traslado); el secuencial se derivaba del
nombre interno de Odoo del picking (`WH/OUT/00001`) en vez de una
secuencia SRI propia; no generaba RIDE, no enviaba por correo, no
manejaba anulación. Solo `l10n_ec.driver`/`l10n_ec.vehicle` estaban
limpios y se reutilizan tal cual en este módulo; el resto se reescribió
contra el esquema real, siguiendo el mismo patrón ya probado end-to-end
de `account.retention` (`l10n_ec_withholding`) para documentos SRI que no
son un `account.move`.

Probado end-to-end contra el SRI de pruebas (`celcer.sri.gob.ec`):
transferencia interna con 2 guías desde un mismo picking, un despacho ya
en estado `done`, y un producto con seguimiento por número de serie --
los tres casos AUTORIZADO. Ver `repos.yaml` para el SHA exacto.
    """,
    "author": "Somatech.dev, egejo (implementación completa desde cero: "
    "el intento previo del upstream nunca se instaló por choque de "
    "nombre técnico y tenía bugs reales; se reescribió siguiendo el "
    "patrón probado de account.retention)",
    "website": "https://github.com/egejo/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": [
        "l10n_ec_base",
        "l10n_ec_edi",
        "l10n_ec_sri",
        "stock",
        "sale_stock",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_ec_delivery_guide_sequence.xml",
        "data/delivery_guide_template.xml",
        "data/mail_template_delivery_guide.xml",
        "report/report_delivery_guide.xml",
        "views/l10n_ec_delivery_guide_views.xml",
        "views/l10n_ec_transport_views.xml",
        "views/stock_picking_views.xml",
        "views/res_company_views.xml",
        "wizard/delivery_guide_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
