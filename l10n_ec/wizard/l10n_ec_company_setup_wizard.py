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
    Auto-carga datos del SRI cuando se ingresa el RUC.
    """
    _name = 'l10n_ec.company.setup.wizard'
    _description = 'Asistente de Configuración de Empresa Ecuador'

    # Search Options
    search_type = fields.Selection([
        ('ruc', 'Buscar por RUC'),
        ('name', 'Buscar por Nombre'),
    ], string='Tipo de Búsqueda', default='ruc')

    search_name = fields.Char(
        string='Buscar por Nombre',
        help='Ingrese el nombre de la empresa para buscar en el SRI'
    )

    # Company Info (auto-loaded from SRI)
    company_ruc = fields.Char(
        string='RUC',
        size=13,
        help='Ingrese el RUC y los datos se cargarán automáticamente del SRI'
    )
    company_name = fields.Char(
        string='Razón Social',
        help='Se carga automáticamente del SRI'
    )
    commercial_name = fields.Char(
        string='Nombre Comercial',
        help='Se carga automáticamente del SRI'
    )

    # Status from SRI
    sri_estado = fields.Char(string='Estado SRI', readonly=True)
    sri_tipo_contribuyente = fields.Char(string='Tipo Contribuyente', readonly=True)
    sri_clase_contribuyente = fields.Char(string='Clase Contribuyente', readonly=True)
    sri_actividad = fields.Char(string='Actividad Económica', readonly=True)

    # Address (auto-loaded)
    street = fields.Char(string='Dirección')
    city = fields.Char(string='Ciudad')
    province = fields.Char(string='Provincia')
    phone = fields.Char(string='Teléfono')
    email = fields.Char(string='Correo Electrónico')
    website = fields.Char(string='Sitio Web')

    # SRI Settings
    sri_environment = fields.Selection([
        ('test', 'Pruebas (Desarrollo)'),
        ('production', 'Producción (Real)'),
    ], string='Ambiente SRI', default='test', required=True)

    obligado_contabilidad = fields.Boolean(
        string='Obligado a Llevar Contabilidad',
        help='Se carga automáticamente del SRI'
    )

    contribuyente_especial = fields.Char(
        string='Nº Contribuyente Especial',
        help='Se carga automáticamente del SRI'
    )

    agente_retencion = fields.Char(
        string='Nº Agente de Retención',
        help='Se carga automáticamente del SRI'
    )

    regimen_rimpe = fields.Char(
        string='Régimen RIMPE',
        readonly=True
    )

    # Status
    sri_loaded = fields.Boolean(string='Datos Cargados del SRI', default=False)
    sri_message = fields.Char(string='Mensaje SRI', readonly=True)

    @api.onchange('company_ruc')
    def _onchange_company_ruc(self):
        """Auto-cargar datos del SRI cuando se ingresa un RUC válido."""
        if not self.company_ruc:
            return

        ruc = self.company_ruc.strip()

        # Solo consultar si tiene 13 dígitos
        if len(ruc) != 13 or not ruc.isdigit():
            self.sri_message = "Ingrese un RUC válido de 13 dígitos"
            self.sri_loaded = False
            return

        # Consultar SRI
        try:
            service = self.env['l10n_ec.sri.ruc.service']
            result = service.consultar_ruc(ruc)

            if result['success']:
                data = result['data']

                # Auto-completar campos
                self.company_name = data.get('razon_social', '')
                self.commercial_name = data.get('nombre_comercial', '')
                self.street = data.get('direccion', '')
                self.city = data.get('canton', '')
                self.province = data.get('provincia', '')
                self.phone = data.get('telefono', '')
                self.email = data.get('email', '')

                # Datos del SRI
                self.sri_estado = data.get('estado', '')
                self.sri_tipo_contribuyente = data.get('tipo_contribuyente', '')
                self.sri_clase_contribuyente = data.get('clase_contribuyente', '')
                self.sri_actividad = data.get('actividad_economica', '')
                self.obligado_contabilidad = data.get('obligado_contabilidad', False)
                self.contribuyente_especial = data.get('contribuyente_especial', '')
                self.agente_retencion = data.get('agente_retencion', '')
                self.regimen_rimpe = data.get('regimen_rimpe', '')

                self.sri_loaded = True
                self.sri_message = f"✅ Datos cargados del SRI - Estado: {data.get('estado', 'N/A')}"

                # Advertir si no está ACTIVO
                if data.get('estado', '').upper() != 'ACTIVO':
                    return {
                        'warning': {
                            'title': 'Contribuyente No Activo',
                            'message': f"El contribuyente tiene estado: {data.get('estado')}. Verifique en el SRI."
                        }
                    }
            else:
                self.sri_loaded = False
                self.sri_message = f"❌ {result.get('error', 'Error desconocido')}"

        except Exception as e:
            self.sri_loaded = False
            self.sri_message = f"❌ Error al consultar SRI: {str(e)}"

    def action_search_by_name(self):
        """Buscar contribuyentes por nombre en el SRI."""
        self.ensure_one()

        if not self.search_name or len(self.search_name) < 3:
            raise ValidationError(_("Ingrese al menos 3 caracteres para buscar"))

        service = self.env['l10n_ec.sri.ruc.service']
        result = service.consultar_por_nombre(self.search_name)

        if not result['success']:
            raise ValidationError(_(result.get('error', 'Error en búsqueda')))

        # Crear registros temporales para selección
        resultados = result['data']

        if len(resultados) == 1:
            # Si solo hay uno, cargar directamente
            self.company_ruc = resultados[0].get('ruc')
            return

        # Si hay múltiples, mostrar lista para seleccionar
        return {
            'type': 'ir.actions.act_window',
            'name': f'Resultados: {self.search_name}',
            'res_model': 'l10n_ec.ruc.search.result',
            'view_mode': 'tree',
            'target': 'new',
            'context': {
                'search_results': resultados,
                'wizard_id': self.id,
            }
        }

    def action_configure_company(self):
        """Aplica la configuración a la empresa."""
        self.ensure_one()

        if not self.company_ruc or not self.company_name:
            raise ValidationError(_("Debe ingresar el RUC y la Razón Social"))

        company = self.env.company
        ecuador = self.env.ref('base.ec')

        # Buscar o crear provincia
        province_id = False
        if self.province:
            province = self.env['res.country.state'].search([
                ('name', 'ilike', self.province),
                ('country_id.code', '=', 'EC')
            ], limit=1)
            province_id = province.id if province else False

        # Update company
        company.write({
            'name': self.company_name,
            'vat': self.company_ruc,
            'company_registry': self.commercial_name or self.company_name,
            'street': self.street,
            'city': self.city,
            'state_id': province_id,
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

        # Success notification
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
        return {'type': 'ir.actions.act_window_close'}
