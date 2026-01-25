# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_ec_rimpe_type = fields.Selection([
        ('none', 'General Regime'),
        ('popular_business', 'RIMPE - Negocio Popular'),
        ('entrepreneur', 'RIMPE - Emprendedor')
    ], string='RIMPE Regime', default='none', help="Tax regime for RIMPE (Art. 97)")

    l10n_ec_rimpe_start_date = fields.Date('RIMPE Start Date')
    l10n_ec_rimpe_end_date = fields.Date('RIMPE End Date')
