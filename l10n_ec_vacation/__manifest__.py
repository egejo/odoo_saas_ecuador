# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Vacation Ledger (Art. 69)",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Statutory Vacation Accrual (15 days + Seniority Bonus)",
    "description": """
Ecuador Vacation Ledger
=======================

Implements **Código del Trabajo Art. 69**:
1. **Base Accrual**: 15 days per year (1.25 days per month).
2. **Seniority Bonus**: From year 6 onwards, +1 day per year.
3. **Ledger System**: Tracks Earned (Gozadas) vs Taken vs Paid (Liquidated).

This module is distinct from standard Odoo Time Off to ensure strict compliance with the "1.25 rule" regardless of work schedule quirks.

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Bug real corregido: la vista de accion usaba `view_mode="tree"` (Odoo
18 lo renombro a "list") y referenciaba un menu padre inexistente
(`l10n_ec_hr_payroll.menu_l10n_ec_hr_payroll_root` en vez del real
`menu_l10n_ec_payroll_root`) -- el menu de este modulo nunca abria.
Corregidos ambos. El calculo de 1.25 dias/mes + bono de antiguedad
sigue SIN probar contra un caso de empleado real.
    """,
    "author": "Somatech.dev, egejo (fork: bug de menú/vista corregido, sin auditar el cálculo con datos reales)",
    "depends": ["l10n_ec_hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/vacation_ledger_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
