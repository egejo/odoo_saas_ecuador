# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Income Tax Engine 2026 (Impuesto Renta)",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "summary": "Progressive Tax Table & Family Loads Rebate (Resolution 00000043)",
    "description": """
Ecuador Income Tax Engine 2026
==============================

Implements the official 2026 logic for **Impuesto a la Renta Personas Naturales**:

1. **Progressive Table (0-37%)**:
   - Resolution NAC-DGERCGC25-00000043.
   - Calculates "Impuesto Causado" on net taxable income.

2. **Rebaja Tributaria (Tax Credit)**:
   - Replaces former "Deductible Expenses".
   - Based on **Family Loads** (Cargas Familiares).
   - Logic: `Min(Expenses, N * Canasta) * 18%`.
   - Handles Catastrophic Diseases (Max Rebate).

This module provides the calculation engine used by `l10n_ec_hr_payroll`.

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Instalado y carga sin error en produccion, con traducciones es_EC
agregadas -- pero, a diferencia de otros modulos de este fork
(l10n_ec_edi/l10n_ec_sri/l10n_ec_withholding/l10n_ec_rimpe), NO ha
sido auditado ni ejercitado con datos reales todavia (falta un
empleado real para probar la tabla progresiva y la rebaja tributaria).
Cada modulo de este fork que si se probo de verdad tuvo al menos un
bug real -- no asumir que este funciona correctamente solo porque
instala limpio.
    """,
    "author": "Somatech.dev, egejo (fork: instalado y traducido, sin auditar funcionalmente todavía)",
    "depends": ["base", "l10n_ec_base"],
    "data": [
        "security/ir.model.access.csv",
        "data/tax_table_2026_data.xml",
        "wizard/gastos_personales_wizard_view.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
