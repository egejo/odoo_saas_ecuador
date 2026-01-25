# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Ley del Sistema Ecuatoriano de Calidad Art. 31-40
# ARCSA Resolución 067 - BPM obligatorio

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityCheck(models.Model):
    """
    Quality Check - Control de Calidad

    Legal basis:
    - Ley Calidad Art. 31-40: Control calidad obligatorio
    - ARCSA Res. 067: BPM para alimentos
    - NTE INEN ISO 9001: Sistema gestión calidad
    """

    _name = "l10n_ec.quality.check"
    _description = "Control de Calidad"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Referencia",
        required=True,
        readonly=True,
        default=lambda self: _("New"),
        copy=False,
    )

    # Related records
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    production_id = fields.Many2one("mrp.production", string="Orden de Producción")
    picking_id = fields.Many2one("stock.picking", string="Transferencia")
    point_id = fields.Many2one("l10n_ec.quality.point", string="Punto de Control")

    # Check details
    check_type = fields.Selection(
        [
            ("visual", "Inspección Visual"),
            ("measure", "Medición"),
            ("sample", "Análisis de Muestra"),
            ("bpm", "Verificación BPM"),
            ("certificate", "Verificación Certificado"),
        ],
        string="Tipo de Control",
        required=True,
        default="visual",
    )

    quality_state = fields.Selection(
        [
            ("none", "Por Realizar"),
            ("pass", "Aprobado"),
            ("fail", "Rechazado"),
        ],
        string="Estado",
        default="none",
        tracking=True,
    )

    # Measurements
    measure_value = fields.Float(string="Valor Medido")
    measure_min = fields.Float(string="Valor Mínimo", related="point_id.measure_min")
    measure_max = fields.Float(string="Valor Máximo", related="point_id.measure_max")

    # Compliance
    inen_norm = fields.Char(string="Norma INEN Aplicable")
    bpm_compliant = fields.Boolean(string="Cumple BPM", default=False)

    # Notes
    notes = fields.Text(string="Observaciones")
    failure_reason = fields.Text(string="Motivo de Rechazo")

    # User
    user_id = fields.Many2one(
        "res.users", string="Inspector", default=lambda self: self.env.user
    )
    check_date = fields.Datetime(string="Fecha Control", default=fields.Datetime.now)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "l10n_ec.quality.check"
                ) or _("New")
        return super().create(vals_list)

    def action_pass(self):
        """Mark quality check as passed."""
        self.write({"quality_state": "pass"})

    def action_fail(self):
        """Mark quality check as failed."""
        if not self.failure_reason:
            raise ValidationError(
                _("Debe indicar el motivo de rechazo antes de rechazar.")
            )
        self.write({"quality_state": "fail"})

    @api.constrains("measure_value", "measure_min", "measure_max")
    def _check_measurement(self):
        """Auto-validate measurement against min/max."""
        for check in self:
            if check.check_type == "measure" and check.point_id:
                if check.measure_min and check.measure_value < check.measure_min:
                    check.quality_state = "fail"
                    check.failure_reason = _(
                        "Valor medido (%.2f) está por debajo del mínimo (%.2f)"
                    ) % (check.measure_value, check.measure_min)
                elif check.measure_max and check.measure_value > check.measure_max:
                    check.quality_state = "fail"
                    check.failure_reason = _(
                        "Valor medido (%.2f) está por encima del máximo (%.2f)"
                    ) % (check.measure_value, check.measure_max)
