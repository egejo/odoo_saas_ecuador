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
decimo tercero/cuarto NO ha sido probada todavia.

Utilidades (Art. 97-104): auditado 2026-07-14, contrario a lo que
decia esta nota antes -- SI esta implementado de verdad (calcula la
utilidad neta desde contabilidad, reparte 10% por dias trabajados y
5% por cargas familiares), no es un placeholder. Se encontro y
corrigio un bug real con datos sinteticos (SAVEPOINT/ROLLBACK): el 5%
se repartia solo por cantidad de cargas, ignorando por completo los
dias trabajados -- un empleado de 1 mes con las mismas cargas que uno
de 12 meses se llevaba la misma proporcion del 5%. Corregido para
ponderar por dias_trabajados x cargas, como exige el Art. 97.

Segundo fix el mismo dia: el campo de cargas familiares que usaba este
reporte (`l10n_ec_family_loads`) era el mismo que usa la rebaja
tributaria de renta (LORTI Art. 10, que SI cuenta padres/madres
dependientes) -- mientras que "cargas familiares" para Utilidades
(Art. 97) solo cuenta conyuge/conviviente e hijos menores de 18 o con
discapacidad, NUNCA padres. Se separo en un campo propio
(`hr.employee.l10n_ec_utilidades_family_loads`, en
`l10n_ec_hr_payroll`) con su propia definicion legal y su propia
vista editable; este reporte ahora lee ese campo nuevo, no el de
renta. El valor viejo no se copio automaticamente al nuevo -- hay que
revisar/completar el nuevo campo por empleado a mano.

Pendiente (fuera de esta ronda, requiere mas alcance): el tope legal
de 24 SBU por trabajador (el excedente va al regimen de prestaciones
solidarias del IESS, NO se redistribuye a otros trabajadores) no esta
implementado -- bajo riesgo real hoy dado el tamaño de la nomina, mas
prioridad si algun empleado se acerca a ese monto.
    """,
    "author": "Somatech.dev, egejo (fork: Utilidades auditada y corregida 2026-07-14; decimo tercero/cuarto instalados y traducidos, sin auditar)",
    "depends": ["l10n_ec_hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sut_report_wizard_view.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
