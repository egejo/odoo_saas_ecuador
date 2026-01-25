# -*- coding: utf-8 -*-
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = "pos.config"

    l10n_ec_sri_active = fields.Boolean(
        string="Active SRI Electronic Invoicing", default=True
    )
    l10n_ec_entity = fields.Char(
        string="Establishment", default="001", help="SRI Establishment Code (e.g. 001)"
    )
    l10n_ec_emission_point = fields.Char(
        string="Emission Point",
        default="001",
        help="SRI Emission Point for this POS (e.g. 002)",
    )
    l10n_ec_default_partner_id = fields.Many2one(
        "res.partner", string="Default Customer (Consumidor Final)"
    )
