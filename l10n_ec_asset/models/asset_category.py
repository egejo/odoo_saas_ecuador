# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# LORTI Art. 28 num. 6 - Depreciación activos fijos

from odoo import models, fields, api


class AssetCategory(models.Model):
    """
    Asset Category - Categoría de Activo Fijo

    Defines depreciation parameters per LORTI Art. 28.
    """

    _name = "l10n_ec.asset.category"
    _description = "Categoría de Activo Fijo"

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(default=True)

    # LORTI Art. 28 depreciation parameters
    depreciation_method = fields.Selection(
        [
            ("linear", "Línea Recta"),
            ("degressive", "Saldos Decrecientes"),
        ],
        string="Método Depreciación",
        default="linear",
        required=True,
    )

    annual_rate = fields.Float(
        string="Tasa Anual (%)",
        required=True,
        help="LORTI Art. 28: Inmuebles 5%, Maquinaria 10%, Vehículos 20%, Equipos cómputo 33%",
    )
    useful_life_years = fields.Integer(
        string="Vida Útil (Años)", compute="_compute_useful_life", store=True
    )

    # Accounts
    asset_account_id = fields.Many2one(
        "account.account",
        string="Cuenta Activo",
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable', 'off_balance'))]",
    )
    depreciation_account_id = fields.Many2one(
        "account.account",
        string="Cuenta Depreciación Acumulada",
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable', 'off_balance'))]",
    )
    expense_account_id = fields.Many2one(
        "account.account",
        string="Cuenta Gasto Depreciación",
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable', 'off_balance'))]",
    )

    journal_id = fields.Many2one("account.journal", string="Diario")

    @api.depends("annual_rate")
    def _compute_useful_life(self):
        for cat in self:
            if cat.annual_rate > 0:
                cat.useful_life_years = int(100 / cat.annual_rate)
            else:
                cat.useful_life_years = 0
