# -*- coding: utf-8 -*-
{
    "name": "Ecuador - SUT Reports (MDT)",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Legal",
    "summary": "Generate TXT/XML for Ministry of Labor (Salarios en Línea)",
    "description": """
Ecuador SUT Reports
===================

Generates compliance files for the **Sistema Único de Trabajo (SUT)**:

1. **13th Salary Report**: TXT for bulk upload.
2. **14th Salary Report**: TXT for bulk upload.
3. **Utilidades**: (Placement for future logic).

Ensures Art. 13 and Art. 14 compliance reporting.

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Instalado y traducido (es_EC), pero la generacion real de TXT de
decimo tercero/cuarto NO ha sido probada todavia. El reporte de
Utilidades sigue siendo un placeholder vacio en el codigo -- no es
"falta probar", es que directamente no esta implementado.
    """,
    "author": "Somatech.dev, egejo (fork: instalado y traducido, sin auditar funcionalmente todavía)",
    "depends": ["l10n_ec_hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sut_report_wizard_view.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
