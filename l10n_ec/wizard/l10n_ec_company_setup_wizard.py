# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Somatech.dev
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re


class L10nEcCompanySetupWizard(models.TransientModel):
    """
    Wizard para configurar la empresa ecuatoriana después de instalar la localización.
    """
    _name = 'l10n_ec.company.setup.wizard'
    _description = 'Asistente de Configuración de Empresa Ecuador'

    # Company Info
    company_name = fields.Char(
        string='Razón Social',
        required=True,
        help='Nombre legal de la empresa registrado en el SRI'
    )
    company_ruc = fields.Char(
        string='RUC',
        required=True,
        size=13,
        help='Registro Único de Contribuyentes (13 dígitos)'
    )
    commercial_name = fields.Char(
        string='Nombre Comercial',
        help='Nombre comercial o marca (opcional)'
    )

    # Address
    street = fields.Char(string='Dirección', required=True)
    city = fields.Char(string='Ciudad', required=True)
    province_id = fields.Many2one(
        'res.country.state',
        string='Provincia',
        domain="[('country_id.code', '=', 'EC')]"
    )
    phone = fields.Char(string='Teléfono')
    email = fields.Char(string='Correo Electrónico', required=True)
    website = fields.Char(string='Sitio Web')

    # SRI Settings
    sri_environment = fields.Selection([
        ('test', 'Pruebas (Desarrollo)'),
        ('production', 'Producción (Real)'),
    ], string='Ambiente SRI', default='test', required=True)

    obligado_contabilidad = fields.Boolean(
        string='Obligado a Llevar Contabilidad',
        default=True,
        help='Marcar si la empresa está obligada a llevar contabilidad'
    )

    contribuyente_especial = fields.Char(
        string='Nº Contribuyente Especial',
        help='Dejar vacío si no es contribuyente especial'
    )

    agente_retencion = fields.Char(
        string='Nº Agente de Retención',
        help='Número de resolución como agente de retención'
    )

    @api.constrains('company_ruc')
    def _check_ruc(self):
        """Valida el RUC ecuatoriano usando Módulo 11."""
        for record in self:
            if record.company_ruc:
                ruc = record.company_ruc.strip()

                # Debe tener 13 dígitos
                if not re.match(r'^\d{13}$', ruc):
                    raise ValidationError(_(
                        "El RUC debe tener exactamente 13 dígitos numéricos.\n"
                        "Ejemplo: 1791234567001"
                    ))

                # Los 3 últimos dígitos deben ser 001
                if ruc[-3:] != '001':
                    raise ValidationError(_(
                        "Los últimos 3 dígitos del RUC deben ser 001.\n"
                        "RUC ingresado: %s"
                    ) % ruc)

                # Validar provincia (primeros 2 dígitos: 01-24)
                provincia = int(ruc[:2])
                if provincia < 1 or provincia > 24:
                    raise ValidationError(_(
                        "Los primeros 2 dígitos del RUC deben ser un código de provincia válido (01-24).\n"
                        "Código ingresado: %s"
                    ) % ruc[:2])

    @api.constrains('email')
    def _check_email(self):
        """Valida formato de correo electrónico."""
        for record in self:
            if record.email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', record.email):
                raise ValidationError(_("El correo electrónico no tiene un formato válido."))

    def action_configure_company(self):
        """Aplica la configuración a la empresa."""
        self.ensure_one()

        company = self.env.company
        ecuador = self.env.ref('base.ec')

        # Update company
        company.write({
            'name': self.company_name,
            'vat': self.company_ruc,
            'company_registry': self.commercial_name or self.company_name,
            'street': self.street,
            'city': self.city,
            'state_id': self.province_id.id if self.province_id else False,
            'country_id': ecuador.id,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
        })

        # Set SRI parameters
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        IrConfigParam.set_param('l10n_ec.sri_environment', self.sri_environment)
        IrConfigParam.set_param('l10n_ec.obligado_contabilidad', str(self.obligado_contabilidad))

        if self.contribuyente_especial:
            IrConfigParam.set_param('l10n_ec.contribuyente_especial', self.contribuyente_especial)

        if self.agente_retencion:
            IrConfigParam.set_param('l10n_ec.agente_retencion', self.agente_retencion)

        # Show success notification and redirect to Settings
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Empresa Configurada'),
                'message': _('La empresa %s ha sido configurada correctamente para Ecuador.') % self.company_name,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'res.config.settings',
                    'view_mode': 'form',
                    'target': 'current',
                }
            }
        }

    def action_skip_wizard(self):
        """Permite saltar el wizard y configurar después."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Configuración Pendiente'),
                'message': _('Puede configurar su empresa en Ajustes > Empresas'),
                'type': 'warning',
                'sticky': False,
            }
        }
