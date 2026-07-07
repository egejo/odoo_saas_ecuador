# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountRetentionLine(models.Model):
    _name = "account.retention.line"
    _description = "Detalle de Retención"

    retention_id = fields.Many2one(
        "account.retention",
        string="Retention",
        required=True,
        ondelete="cascade",
        index=True,
    )
    currency_id = fields.Many2one(related="retention_id.currency_id")

    # Tax Information: el tipo usa el mismo vocabulario que
    # l10n_ec.withholding.tax.type ("renta"/"iva"/"isd"), no el codigo
    # numerico de la Tabla 16 del SRI (1/2/6) -- antes se comparaban aqui
    # los dos vocabularios distintos ("1"/"2"/"6" vs "renta"/"iva"/"isd"),
    # asi que el dominio de tax_id nunca encontraba ninguna coincidencia
    # y el campo (requerido) quedaba imposible de completar. El mapeo al
    # codigo SRI (1/2/6) para el XML vive en account_retention.py.
    tax_type = fields.Selection(
        [
            ("renta", "Impuesto a la Renta (Tabla 19)"),
            ("iva", "IVA (Tabla 21)"),
            ("isd", "ISD"),
        ],
        string="Impuesto",
        required=True,
    )

    tax_id = fields.Many2one(
        "l10n_ec.withholding.tax",
        string="Código de Retención",
        required=True,
        domain="[('type', '=', tax_type)]",
    )

    # Related fields for ease of use/display
    tax_code = fields.Char(
        related="tax_id.code", string="Código", store=True, readonly=True
    )
    percentage = fields.Float(
        related="tax_id.percentage", string="Porcentaje %", store=True, readonly=True
    )

    base = fields.Monetary(string="Base Imponible", required=True)
    amount = fields.Monetary(
        string="Valor Retenido", required=True, compute="_compute_amount", store=True
    )

    # Document Sustento (if multi-invoice retention allowed, usually 1-to-1 but data structure supports N)
    invoice_id = fields.Many2one("account.move", string="Invoice Reference")

    @api.depends("base", "percentage")
    def _compute_amount(self):
        for line in self:
            line.amount = line.base * (line.percentage / 100.0)
