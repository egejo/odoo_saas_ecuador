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

✅ **Contabilidad (l10n_ec_base)**
   - Plan de Cuentas NEC/NIIF
   - Impuestos IVA 15%, 5%, 0%
   - Validación RUC/Cédula

✅ **Facturación Electrónica (l10n_ec_edi + l10n_ec_sri)**
   - Generación XML
   - Firma XAdES-BES
   - Transmisión SRI
   - RIDE PDF

✅ **Retenciones (l10n_ec_withholding)**
   - Retención IR e IVA
   - Regla de 5 días

✅ **Punto de Venta (l10n_ec_pos)**
   - Facturación electrónica en POS

✅ **Inventario (l10n_ec_stock)**
   - Guía de Remisión electrónica

✅ **Reportes (l10n_ec_reports)**
   - ATS
   - Formulario 104

✅ **Nómina (l10n_ec_hr_payroll)**
   - IESS (9.45% / 12.15%)
   - Décimo Tercero y Cuarto
   - Utilidades 15%

✅ **Aduanas (l10n_ec_customs)**
   - DAU
   - Partidas Arancelarias
   - FODINFA, IVA Importación

🔧 **CONFIGURACIÓN AUTOMÁTICA**:
   - Idioma: Español Ecuador
   - País: Ecuador
   - Moneda: USD
   - Zona horaria: America/Guayaquil
   - SBU 2026: $482
   - IVA: 15%

**Cumple 100% con regulaciones SRI, IESS, Min. Trabajo 2026**

Desarrollado por Somatech.dev
    """,
    'author': 'Somatech.dev, Odoo Community Association (OCA)',
    'website': 'https://github.com/somatechlat/odoo_saas_ecuador',
    'license': 'LGPL-3',
    'depends': [
        # Core modules
        'l10n_ec_base',
        'l10n_ec_edi',
        'l10n_ec_sri',
        # Functional modules
        'l10n_ec_withholding',
        'l10n_ec_stock',
        'l10n_ec_pos',
        'l10n_ec_reports',
        # HR & Customs
        'l10n_ec_hr_payroll',
        'l10n_ec_customs',
    ],
    'data': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
    'post_init_hook': 'hooks.post_init_hook',
    'uninstall_hook': 'hooks.uninstall_hook',
}
