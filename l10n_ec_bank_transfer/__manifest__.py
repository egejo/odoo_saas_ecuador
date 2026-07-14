# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Bank Cash Management (Pichincha/Guayaquil)",
    "version": "18.0.1.1.0",
    "category": "Human Resources/Payroll",
    "summary": "Generate TXT files for Bulk Payroll Payments",
    "description": """
Ecuador Bank Transfer - Cash Management
=======================================

**The Fragata ERP Killer Feature.**
Generates the specific `.txt` files required by Ecuadorian banks for bulk payroll transfers.

Supported Banks:
1.  **Banco Pichincha** (Cash Management Carga de Pagos)
2.  **Banco Guayaquil** (Multicash)

Usage:
1.  Select Payslips in List View.
2.  Action > Generate Cash Management File.
3.  Upload to Bank Portal.

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Auditado y probado 2026-07-14 con datos sinteticos (SAVEPOINT/ROLLBACK):
- **Pichincha crasheaba SIEMPRE**: `_generate_pichincha_txt` referenciaba
  `slip.number`, un campo que no existe en `l10n_ec.payslip` (nunca se
  habia ejecutado antes) -- `AttributeError` garantizado. Corregido a
  `slip.name` (el identificador real del payslip).
- **Formato de monto equivocado**: el codigo escribia el valor con punto
  decimal ("534.58"); la ayuda oficial de Pichincha Cash Management
  publicada por el banco especifica que el VALOR va SIN coma ni punto
  decimal (los ultimos 2 digitos son los centavos, ej. "53458").
  Corregido. Se agregaron ademas TIPO ID (C/R/P, campo nuevo
  `hr.employee.l10n_ec_bank_id_type`) y distincion real CTA/AHO (campo
  nuevo `res.partner.bank.l10n_ec_account_type`, antes siempre asumia
  "AHO" sin importar el tipo real de cuenta), tal como exige el
  instructivo.
- **Guayaquil era un stub no funcional**: solo escribia
  "Nombre,ImporteConDecimalesDeMas" sin cedula, sin cuenta bancaria, sin
  referencia, y con un nombre de archivo inventado. Corregido con los
  elementos que si se pudieron confirmar contra la ayuda oficial
  (Referencia obligatoria, Codigo=identificacion del beneficiario, datos
  de cuenta para acreditar, convencion de nombre de archivo real
  `PAGOS_MULTICASH_AAAAMMDD_SS.TXT`).
- Se agrego un guard que bloquea la generacion (`UserError` claro, no
  un archivo con cuenta placeholder "0000000000") si algun empleado
  seleccionado no tiene cuenta bancaria configurada -- antes se hubiera
  generado un archivo real con una cuenta inventada, arriesgando una
  transferencia real a un destino invalido.

**Importante, sigue sin confirmarse al 100%**: los PDFs instructivos
oficiales de ambos bancos (Pichincha "Formato carga de ordenes de pago
masiva", Guayaquil "Guia para elaboracion de archivo de pagos") vienen
escaneados como imagenes, sin texto extraible en este entorno -- las
correcciones de arriba se confirmaron contra fragmentos de la ayuda
oficial de cada banco (articulos de su centro de ayuda, no el PDF
completo), no contra el layout completo y exacto (delimitador preciso,
orden completo de columnas, estructura de header/footer). **No usar
este archivo para un pago real sin validarlo antes contra el
instructivo completo o el generador de TXT que el propio Banco
Guayaquil publica en su Banca Empresas.**
    """,
    "author": "Somatech.dev, egejo (fork: crash de Pichincha corregido, formato de monto/TIPO ID/CTA corregido contra ayuda oficial, Guayaquil dejo de ser un stub -- 2026-07-14; layout completo aun sin confirmar al 100%)",
    "depends": ["l10n_ec_hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/bank_transfer_view.xml",
        "views/res_partner_bank_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
