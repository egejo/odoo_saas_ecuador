# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_ec_sri_environment = fields.Selection(
        [
            ('1', 'Test (Pruebas)'),
            ('2', 'Production (Producción)')
        ],
        string='SRI Environment',
        default='1',
        help='Environment for Electronic Invoicing'
    )

    l10n_ec_certificate_id = fields.Many2one(
        'l10n_ec.certificate',
        string='Electronic Signature',
        domain="[('company_id', '=', id), ('state', '=', 'active')]",
        help='The active digital signature for this company'
    )

    l10n_ec_sri_reception_url = fields.Char(
        string='Reception WSDL',
        default='https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
    )

    l10n_ec_sri_authorization_url = fields.Char(
        string='Authorization WSDL',
        default='https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
    )
