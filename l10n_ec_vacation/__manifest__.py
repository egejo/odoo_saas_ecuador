# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Vacation Ledger (Art. 69)",
    "version": "18.0.1.1.0",
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
Corregidos ambos.

Auditado con datos sintéticos 2026-07-14 (SAVEPOINT/ROLLBACK), 0
registros reales en producción (nunca se había corrido). El cálculo de
1.25 días/mes + bono de antigüedad (tope 15 días adicionales, 30
días/año máximo -- confirmado real contra el texto del Art. 69 via
búsqueda web, la duda que el propio código original dejaba en un
comentario SÍ era correcta) da el resultado esperado. Pero se
encontraron y corrigieron 3 bugs reales:
1. **`run_monthly_accrual` nunca se ejecutaba solo** -- no existía
   ningún `ir.cron` que lo invocara, ni botón, ni ninguna otra vía. La
   funcionalidad central del módulo ("ledger automático") jamás
   generaba una sola línea sin intervención manual por consola. Se
   agregó un `ir.cron` mensual real.
2. **Sin protección contra duplicados** (reconocido en el propio
   comentario original: "Omitted for MVP simplicity") -- correr el
   método dos veces en el mismo mes (cron duplicado, corrida manual
   repetida) duplicaba el devengo de cada contrato activo,
   silenciosamente. Corregido con un campo marcador
   (`is_monthly_accrual`) + chequeo antes de crear.
3. **El "balance" no era un saldo corriente real**: `_compute_balance`
   sumaba TODAS las líneas del empleado sin filtrar por fecha, así que
   cada fila mostraba el mismo gran total -- y ese total quedaba
   congelado en las líneas viejas (el compute de un registro no se
   re-dispara cuando se crea/edita un hermano). Probado: crear 3 líneas
   en orden mostraba la 1ra línea con balance=1.25 para siempre, aunque
   las líneas 2 y 3 ya hubieran cambiado el saldo real. Corregido para
   calcular un saldo corriente cronológico real, con `create`/`write`/
   `unlink` forzando el recálculo de todas las líneas hermanas del
   mismo empleado cuando corresponde.
    """,
    "author": "Somatech.dev, egejo (fork: bug de menú/vista corregido; cron de devengo agregado, dedup y saldo corriente real corregidos 2026-07-14)",
    "depends": ["l10n_ec_hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/vacation_ledger_views.xml",
        "data/ir_cron_data.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
