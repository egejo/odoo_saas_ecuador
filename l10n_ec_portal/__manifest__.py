# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Employee Portal (Self-Service)",
    "version": "18.0.1.2.0",
    "category": "Human Resources",
    "summary": "Payslips and Loans for Employees in Website Portal",
    "description": """
Ecuador Employee Portal
=======================

**The PacERP Killer Feature.**
Allows employees to log in (website user) and:
1.  View and Download their **Payslips (Rol de Pagos)**.
2.  View their **Loans** status.

Surpasses competitor "Ease of Use" by eliminating HR email requests.

--------------------------------------------------------------------
Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
--------------------------------------------------------------------
Auditado 2026-07-14 con un usuario de portal sintetico real (creado y
enlazado via `hr.employee.user_id`, no solo revisando codigo) -- se
encontraron y corrigieron 3 bugs reales, los 3 confirmados con
`AccessError`/`AttributeError` reales antes del fix:

1. **`security/ir.model.access.csv` estaba completamente vacio** (solo
   el encabezado) -- los modelos `l10n_ec.payslip`/`l10n_ec.loan` solo
   tienen permisos para `base.group_user` (usuarios internos); un
   usuario de portal (`base.group_portal`, un grupo totalmente
   distinto) no tenia NINGUN acceso. Cualquier ruta de este modulo
   (`/my/payslips`, `/my/loans`, los contadores del home del portal)
   fallaba con `AccessError` para cualquier empleado real. Corregido
   con accesos de solo lectura para `base.group_portal`, mas reglas de
   registro (`ir.rule`) que restringen cada consulta al propio
   empleado del usuario (`employee_id.user_id = user.id`) -- sin esto
   ultimo, otorgar el acceso a nivel de modelo hubiera dejado a
   cualquier empleado con portal ver el rol de pagos de CUALQUIER
   otro, un problema de seguridad real, no solo un bug de acceso
   denegado.
2. **La vista de detalle del rol de pagos crasheaba siempre**:
   `payslip.company_id` -- `l10n_ec.payslip` no tiene ese campo (la
   vista de lista usaba, en cambio, `payslip.employee_id.company_id`,
   que resulto tener su propio problema real, ver mas abajo).
3. **El boton "Descargar PDF" apuntaba a un reporte que nunca existio**
   (`l10n_ec_hr_payroll.report_payslip`) -- el modulo de nomina solo
   tenia el reporte de Formulario 107, ningun PDF de rol de pagos en
   si. Se agrego un reporte real en `l10n_ec_hr_payroll`
   (`action_report_payslip`).
4. **Bug de plataforma real, encontrado ya con el acceso corregido**:
   `payslip.employee_id.company_id` (usado en la vista de lista, y
   copiado a la de detalle) revienta con `AccessError` bajo un usuario
   de portal si el lote de prefetch de Odoo sobre `hr.employee`
   arrastra OTRO registro (de otro empleado) ya en cache cuyos campos
   no son visibles para "perfiles publicos" -- un campo restringido ahi
   tumba el lote completo. Solucionado en `l10n_ec_hr_payroll` con 3
   campos `related(store=True)` en el propio `l10n_ec.payslip`
   (`company_id`, `employee_name`, `employee_identification_id`), asi
   el portal nunca vuelve a tocar `hr.employee` al leer. De paso,
   `employee_identification_id` necesito `groups=""` explicito porque
   heredaba el `groups="hr.group_hr_user"` de
   `hr.employee.identification_id` -- sin eso, un empleado no podia ver
   su propia cedula en su propio rol de pagos.

Probado end-to-end con datos sinteticos (dos empleados+contratos+
payslips+prestamos+usuarios de portal distintos, para forzar el caso
de prefetch cruzado que reproducia el bug 4): contador del home,
listado de roles de pago, detalle de un rol de pago, descarga real de
PDF (45923 bytes generados) y listado de prestamos, todos funcionando
bajo la identidad real de un usuario de portal (`env(user=...)`, no
sudo) -- y confirmado que el usuario de portal de OTRO empleado no
puede leer estos registros ni por ID directo ni por busqueda (la
`ir.rule` bloquea correctamente en ambos casos).
    """,
    "author": "Somatech.dev, egejo (fork: acceso de portal, crash de company_id y reporte PDF faltante corregidos 2026-07-14, probado end-to-end con un usuario de portal real)",
    "depends": [
        "portal",
        "l10n_ec_hr_payroll",
        "l10n_ec_loans",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/l10n_ec_portal_security.xml",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
