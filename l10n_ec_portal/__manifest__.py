# -*- coding: utf-8 -*-
{
    "name": "Ecuador - Employee Portal (Self-Service)",
    "version": "18.0.1.0.0",
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
Instalado, pero SIN crear todavia ningun usuario de portal para un
empleado real -- no se ha confirmado que pueda ver/descargar su rol de
pagos ni el estado de sus prestamos.
    """,
    "author": "Somatech.dev, egejo (fork: instalado, sin auditar funcionalmente todavía)",
    "depends": [
        "portal",
        "l10n_ec_hr_payroll",
        "l10n_ec_loans",
    ],
    "data": [
        "views/portal_templates.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
