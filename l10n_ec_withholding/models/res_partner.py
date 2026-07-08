# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Campos requeridos por el SRI en el comprobante de retencion cuando
    # el proveedor es del exterior (tipoIdentificacionSujetoRetenido
    # '08'): pagoLocExt pasa a '02' y el schema exige ademas tipoRegi/
    # paisEfecPago/aplicConvDobTrib (ver account_retention.py,
    # action_send_sri, y retention_template.xml). No hay catalogo de
    # paises SRI cargado en este sistema (l10n_ec_code_ats/
    # l10n_ec_code_tax_haven son campos exclusivos de Enterprise en
    # res.country, no existen en Community) -- se piden a mano en vez de
    # adivinar, para no transmitir un dato incorrecto al SRI.
    l10n_ec_withhold_foreign_country_code = fields.Char(
        string="Código País SRI",
        help="Código de país de la Tabla de Codificación de Países del "
        "SRI. Requerido en el comprobante de retención cuando este "
        "proveedor es del exterior. Verificar el código correcto en la "
        "ficha técnica de comprobantes electrónicos del SRI.",
    )
    l10n_ec_withhold_foreign_regime = fields.Selection(
        [
            ("01", "Régimen General"),
            ("02", "Régimen Fiscal Preferente o de Menor Imposición"),
            ("03", "Paraíso Fiscal"),
        ],
        string="Tipo de Régimen Fiscal",
        default="01",
        help="Tabla del SRI para comprobantes de retención a "
        "proveedores del exterior (tipoRegi).",
    )
    l10n_ec_withhold_double_taxation = fields.Boolean(
        string="Aplica Convenio de Doble Tributación",
        help="Marcar si existe un convenio de doble tributación vigente "
        "entre Ecuador y el país de este proveedor.",
    )
