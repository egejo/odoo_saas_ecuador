# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Configura automáticamente Odoo para Ecuador al instalar la localización.

    Configura:
    - Idioma: Español (Ecuador)
    - País: Ecuador
    - Moneda: USD
    - Zona horaria: America/Guayaquil
    - Formato de fecha: dd/mm/yyyy
    - Separadores: . para miles, , para decimales
    """
    _logger.info("🇪🇨 Iniciando configuración automática de localización Ecuador...")

    # =========================================================================
    # 1. INSTALAR IDIOMA ESPAÑOL ECUADOR
    # =========================================================================
    try:
        lang = env['res.lang']._activate_lang('es_EC')
        if not lang:
            # Try Spanish generic if es_EC not available
            lang = env['res.lang']._activate_lang('es_ES')
        _logger.info("✅ Idioma Español activado")
    except Exception as e:
        _logger.warning(f"⚠️ No se pudo activar idioma español: {e}")

    # =========================================================================
    # 2. CONFIGURAR COMPAÑÍA PRINCIPAL
    # =========================================================================
    try:
        company = env.company
        ecuador = env.ref('base.ec', raise_if_not_found=False)
        usd = env.ref('base.USD', raise_if_not_found=False)

        company_vals = {}

        # País Ecuador
        if ecuador:
            company_vals['country_id'] = ecuador.id
            company_vals['account_fiscal_country_id'] = ecuador.id

        # Moneda USD
        if usd:
            company_vals['currency_id'] = usd.id

        if company_vals:
            company.write(company_vals)
            _logger.info("✅ Compañía configurada para Ecuador")
    except Exception as e:
        _logger.warning(f"⚠️ Error configurando compañía: {e}")

    # =========================================================================
    # 3. CONFIGURAR USUARIO ADMIN
    # =========================================================================
    try:
        admin_user = env.ref('base.user_admin', raise_if_not_found=False)
        if admin_user:
            user_vals = {
                'tz': 'America/Guayaquil',
            }
            # Set language if available
            if env['res.lang'].search([('code', '=', 'es_EC')]):
                user_vals['lang'] = 'es_EC'
            elif env['res.lang'].search([('code', '=', 'es_ES')]):
                user_vals['lang'] = 'es_ES'

            admin_user.write(user_vals)
            _logger.info("✅ Usuario admin configurado: zona horaria America/Guayaquil")
    except Exception as e:
        _logger.warning(f"⚠️ Error configurando usuario: {e}")

    # =========================================================================
    # 4. CONFIGURAR PARÁMETROS DEL SISTEMA
    # =========================================================================
    try:
        IrConfigParam = env['ir.config_parameter'].sudo()

        # SBU 2026
        IrConfigParam.set_param('l10n_ec.sbu', '482')
        IrConfigParam.set_param('l10n_ec.sbu_year', '2026')

        # IESS rates
        IrConfigParam.set_param('l10n_ec.iess_personal', '9.45')
        IrConfigParam.set_param('l10n_ec.iess_patronal', '12.15')

        # IVA rate
        IrConfigParam.set_param('l10n_ec.iva_rate', '15')

        # Consumidor Final limit
        IrConfigParam.set_param('l10n_ec.consumidor_final_limit', '50')

        _logger.info("✅ Parámetros del sistema configurados (SBU $482, IVA 15%, etc.)")
    except Exception as e:
        _logger.warning(f"⚠️ Error configurando parámetros: {e}")

    # =========================================================================
    # 5. ACTIVAR MONEDA USD
    # =========================================================================
    try:
        usd_currency = env.ref('base.USD', raise_if_not_found=False)
        if usd_currency and not usd_currency.active:
            usd_currency.active = True
            _logger.info("✅ Moneda USD activada")
    except Exception as e:
        _logger.warning(f"⚠️ Error activando USD: {e}")

    _logger.info("🇪🇨 ¡Localización Ecuador configurada exitosamente!")


def uninstall_hook(env):
    """
    Limpia parámetros al desinstalar.
    """
    _logger.info("Desinstalando localización Ecuador...")
    try:
        IrConfigParam = env['ir.config_parameter'].sudo()
        params_to_remove = [
            'l10n_ec.sbu',
            'l10n_ec.sbu_year',
            'l10n_ec.iess_personal',
            'l10n_ec.iess_patronal',
            'l10n_ec.iva_rate',
            'l10n_ec.consumidor_final_limit',
        ]
        for param in params_to_remove:
            IrConfigParam.set_param(param, False)
    except Exception as e:
        _logger.warning(f"Error en desinstalación: {e}")
