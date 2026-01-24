# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': '🇪🇨 Ecuador - Localización Completa',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Instala TODA la localización Ecuador con un solo clic - SRI 2026, IESS, Aduanas',
    'description': """
🇪🇨 Localización Ecuador Completa para Odoo 18
==============================================

Este módulo instala **TODA** la localización ecuatoriana con **UN SOLO CLIC**:

✅ **Contabilidad** - Plan de Cuentas NEC/NIIF, IVA 15%/5%/0%
✅ **Facturación Electrónica** - XML, XAdES-BES, SRI, RIDE
✅ **Retenciones** - IR, IVA, Regla 5 días
✅ **Punto de Venta** - Facturación POS
✅ **Inventario** - Guía de Remisión
✅ **Reportes** - ATS, Formulario 104
✅ **Nómina** - IESS, Décimos, Utilidades
✅ **Aduanas** - DAU, FODINFA

🔧 **CONFIGURACIÓN AUTOMÁTICA**:
   - Asistente de configuración de empresa
   - Idioma: Español Ecuador
   - País: Ecuador
   - Moneda: USD
   - Zona horaria: America/Guayaquil
   - SBU 2026: $482
   - IVA: 15%

Desarrollado por Somatech.dev
    """,
    'author': 'Somatech.dev, Odoo Community Association (OCA)',
    'website': 'https://github.com/somatechlat/odoo_saas_ecuador',
    'license': 'LGPL-3',
    'depends': [
        'l10n_ec_base',
        'l10n_ec_edi',
        'l10n_ec_sri',
        'l10n_ec_withholding',
        'l10n_ec_stock',
        'l10n_ec_pos',
        'l10n_ec_reports',
        'l10n_ec_hr_payroll',
        'l10n_ec_customs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/l10n_ec_company_setup_wizard_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
