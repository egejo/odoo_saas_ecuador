# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# NTE INEN ISO 9001 - Quality Control Points

from odoo import models, fields


class QualityPoint(models.Model):
    """
    Quality Control Point - Punto de Control de Calidad

    Defines where quality checks should be performed.
    Based on NTE INEN ISO 9001 requirements.
    """

    _name = "l10n_ec.quality.point"
    _description = "Punto de Control de Calidad"

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(default=True)

    # Where this point applies
    product_ids = fields.Many2many("product.product", string="Productos")
    product_category_ids = fields.Many2many("product.category", string="Categorías")
    picking_type_ids = fields.Many2many(
        "stock.picking.type", string="Tipos de Operación"
    )

    # When to trigger
    trigger = fields.Selection(
        [
            ("receipt", "Al Recibir"),
            ("delivery", "Al Entregar"),
            ("production_start", "Al Iniciar Producción"),
            ("production_end", "Al Finalizar Producción"),
        ],
        string="Disparador",
        required=True,
        default="receipt",
    )

    # Check configuration
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

    # For measurement checks
    measure_min = fields.Float(string="Valor Mínimo")
    measure_max = fields.Float(string="Valor Máximo")
    measure_unit = fields.Char(string="Unidad de Medida")

    # INEN/ARCSA reference
    inen_norm = fields.Char(string="Norma INEN")
    arcsa_requirement = fields.Char(string="Requisito ARCSA")

    # Instructions
    instructions = fields.Html(string="Instrucciones de Control")

    # Counts
    check_count = fields.Integer(compute="_compute_check_count")

    def _compute_check_count(self):
        for point in self:
            point.check_count = self.env["l10n_ec.quality.check"].search_count(
                [("point_id", "=", point.id)]
            )
