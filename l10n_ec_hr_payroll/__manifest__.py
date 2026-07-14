# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Ecuador - Payroll (IESS, Décimos, Utilidades)",
    "version": "18.0.1.2.0",
    "category": "Human Resources/Payroll",
    "summary": "Complete Ecuadorian payroll with IESS, Décimos, and Utilidades",
    "description": """
Ecuadorian Payroll Localization
===============================

Complete payroll management for Ecuador (SBU 2026: $482):

* IESS Contributions
  - Personal: 9.45%
  - Patronal: 11.15% (base IESS) + SECAP 0.5% + IECE 0.5% = 12.15% total
* Décimo Tercero (13th Salary) - Due December 24
* Décimo Cuarto (14th Salary)
  - Costa/Galápagos: March 15
  - Sierra/Amazonía: August 15
* Fondos de Reserva (8.33% after 13 months)
* Utilidades (15% profit sharing - April 15)
* Overtime calculations (50%, 100%, 25%)
* Income Tax (Impuesto a la Renta)

**Regulatory Compliance**: Ministerio del Trabajo 2026, IESS 2026

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Bug real de empaquetado corregido: este modulo redeclaraba claves de
`ir.config_parameter` (aporte personal/patronal IESS, etc.) ya
registradas por `l10n_ec_base` con el mismo valor pero violando la
constraint de unicidad, bloqueando la instalacion junto a otros 10
modulos. Corregido. Ademas, un menu padre inexistente
(`l10n_ec_hr_payroll.menu_l10n_ec_hr_payroll_root`, el real es
`menu_l10n_ec_payroll_root`) era referenciado por otros modulos de
este fork (`l10n_ec_loans`/`l10n_ec_vacation`) y causaba el mismo tipo
de fallo -- corregido ahi.

Bug real de calculo encontrado el 2026-07-13, probando el primer
payslip real (empleado+contrato sinteticos, SAVEPOINT/ROLLBACK):
`l10n_ec.payslip._compute_totals` calcula `total_income` = 0 sin
importar el sueldo del contrato, y por lo tanto TODO lo que depende de
el (IESS personal/patronal, impuesto a la renta, decimo tercero, fondos
de reserva, neto) tambien queda en 0 -- solo el decimo cuarto (que no
depende de total_income) calculaba bien. Causa raiz: `_compute_totals`
llama a `_compute_overtime_from_attendance()`, que busca en el modelo
`hr.attendance` -- pero `hr_attendance` nunca estaba declarado como
dependencia del manifiesto ni instalado en este servidor, asi que ese
modelo no existe en el registro. Se agrego `hr_attendance` a `depends`.
Con esto, la funcion de auto-calculo de horas extra desde biometrico/
kiosko (ya presente en el codigo, sin usar hasta ahora) puede funcionar
de verdad si se activa el control de asistencia.

Bug real encontrado auditando Utilidades el 2026-07-14 (ver
l10n_ec_sut): el unico campo `l10n_ec_family_loads` (Cargas
Familiares) se usaba tanto para la rebaja de impuesto a la renta
(LORTI Art. 10, que SI cuenta padres/madres dependientes) como para el
5% de Utilidades (Codigo de Trabajo Art. 97, que NO cuenta padres,
solo conyuge/hijos <18 o con discapacidad) -- un empleado con un padre
a cargo pero sin conyuge/hijos hubiera recibido de mas en Utilidades.
Se agrego un campo separado `l10n_ec_utilidades_family_loads` con su
propia definicion legal, y una vista nueva (antes ninguno de estos
campos era editable desde la UI, solo por ORM) para que ambos se vean
y editen por separado en la ficha del empleado. No se copio el valor
del campo viejo al nuevo automaticamente (arrastraria el mismo error
que se esta corrigiendo) -- revisar/completar el nuevo campo por
empleado a mano.

Auditando el portal de empleado (`l10n_ec_portal`) el 2026-07-14 se
encontro que su boton "Descargar PDF" del rol de pagos apuntaba a un
reporte (`l10n_ec_hr_payroll.report_payslip`) que nunca existio en
este modulo -- solo existia `action_report_form_107` (Formulario 107).
Se agrego un reporte real (`action_report_payslip`, QWeb) con el
desglose de ingresos/egresos y neto a recibir.

Probando ese reporte/portal bajo la identidad real de un usuario de
portal (no sudo) aparecio un bug de plataforma real, no de este fork:
leer `payslip.employee_id.company_id` (o cualquier campo de
`hr.employee`) desde un contexto de portal puede reventar con
`AccessError` si el lote de prefetch de Odoo arrastra OTRO registro de
`hr.employee` ya en cache (de otro empleado) cuyos campos no son
visibles para "perfiles publicos" -- un solo campo restringido ahi
tumba el lote completo, aunque el campo pedido no sea sensible.
Solucion: se agregaron 3 campos `related(store=True)` directamente en
`l10n_ec.payslip` (`company_id`, `employee_name`,
`employee_identification_id`), para que el portal/reporte nunca
necesite volver a tocar `hr.employee` al momento de leer. De paso,
`employee_identification_id` necesito `groups=""` explicito: un campo
`related` hereda automaticamente el `groups="hr.group_hr_user"` de
`hr.employee.identification_id`, y sin anularlo un empleado no podia
ver su propia cedula en su propio rol de pagos (correctamente
restringido a el mismo por el `ir.rule` de `l10n_ec_portal`).
    """,
    "author": "Somatech.dev, Odoo Community Association (OCA), egejo (fork: bug de empaquetado corregido, payslip real corregido 2026-07-13, cargas familiares de Utilidades separadas 2026-07-14, reporte PDF de rol de pagos agregado 2026-07-14)",
    "website": "https://github.com/somatechlat/odoo_saas_ecuador",
    "license": "LGPL-3",
    "depends": ["hr", "hr_contract", "hr_attendance"],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_ec_salary_rule_data.xml",
        "data/l10n_ec_payroll_data.xml",
        "report/form_107_template.xml",
        "report/payslip_report_template.xml",
        "views/hr_contract_views.xml",
        "views/l10n_ec_payslip_views.xml",
        "views/hr_employee_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
}
