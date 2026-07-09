# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Loans & IESS Extension",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Manage Company Loans and IESS Deductions",
    "description": """
Ecuador Loans
=============

1. **IESS Import**: Wizard to upload CSV/TXT from IESS for Quirografario/Hipotecario loans.
2. **Loan Management**: Track installments and status.
3. **Payslip Integration**: Automatically deducts due installments from the employee's payslip.

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Bug real corregido: la vista de accion usaba `view_mode="tree"` (Odoo
18 lo renombro a "list") y referenciaba un menu padre inexistente
(`l10n_ec_hr_payroll.menu_l10n_ec_hr_payroll_root` en vez del real
`menu_l10n_ec_payroll_root`) -- el menu de este modulo nunca abria.
Corregidos ambos. El wizard de importacion IESS y el descuento
automatico en el rol de pagos siguen SIN probar con un archivo real.
    """,
    "author": "Somatech.dev, egejo (fork: bug de menú/vista corregido, sin auditar el flujo completo con datos reales)",
    "depends": ["l10n_ec_hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/loan_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
