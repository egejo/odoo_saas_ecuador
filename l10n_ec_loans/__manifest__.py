# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Loans & IESS Extension",
    "version": "18.0.1.1.0",
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
Corregidos ambos.

Bug real critico encontrado el 2026-07-13, probando el primer payslip
real (empleado+contrato sinteticos, SAVEPOINT/ROLLBACK): este modulo
redefinia `_compute_totals` -- el mismo nombre de metodo que
`l10n_ec_hr_payroll` ya usa para calcular `total_income`/`income_tax`/
`net_wage` -- sin llamar a `super()`. En la resolucion de metodos de
Python, la version de este modulo (cargado despues) reemplazaba por
completo la del modulo base, asi que CUALQUIER rol de pagos con
`l10n_ec_loans` instalado (que es el caso normal, ya que el modulo
provee el descuento automatico de prestamos) quedaba con
`total_income`/`income_tax` siempre en 0 -- sin excepcion, sin aviso,
en cualquier instalacion real. Solo `net_wage` calculaba (mal, usando
total_income=0). Corregido: se redeclara el campo `net_wage` con su
propio metodo de compute (`_compute_net_wage_with_loans`) en vez de
reusar el nombre `_compute_totals`, dejando intacto el calculo original
de `total_income`/`income_tax` del modulo base.
    """,
    "author": "Somatech.dev, egejo (fork: bug de menú/vista corregido; bug critico de calculo de nomina corregido 2026-07-13)",
    "depends": ["l10n_ec_hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/loan_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
