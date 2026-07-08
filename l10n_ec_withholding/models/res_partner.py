# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Campos requeridos por el SRI en el comprobante de retencion cuando
    # el proveedor es del exterior (tipoIdentificacionSujetoRetenido
    # '08'): pagoLocExt pasa a '02' y el schema exige ademas tipoRegi/
    # paisEfecPago/aplicConvDobTrib (ver account_retention.py,
    # action_send_sri, y retention_template.xml). l10n_ec_base ya trae
    # el catalogo de paises del SRI (res.country.l10n_ec_code_ats, ver
    # l10n_ec_base/models/res_country.py) -- este campo se autocompleta
    # desde ahi via onchange y solo hace falta tocarlo a mano si el pais
    # no esta en el catalogo o el SRI cambio el codigo y el catalogo del
    # modulo todavia no se actualizo.
    l10n_ec_withhold_foreign_country_code = fields.Char(
        string="Código País SRI",
        help="Código de país de la Tabla de Codificación de Países del "
        "SRI. Requerido en el comprobante de retención cuando este "
        "proveedor es del exterior. Se autocompleta desde el catálogo "
        "de países (Contactos > Configuración > Países) según el país "
        "de este contacto; editar solo si falta en el catálogo.",
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

    @api.onchange("country_id")
    def _onchange_country_id_l10n_ec_withhold_foreign_country_code(self):
        # Solo autocompleta si esta vacio: no pisar un valor que el
        # usuario ya haya cargado a mano (caso pais fuera del catalogo,
        # o codigo SRI corregido manualmente).
        for partner in self:
            if not partner.l10n_ec_withhold_foreign_country_code and partner.country_id.l10n_ec_code_ats:
                partner.l10n_ec_withhold_foreign_country_code = partner.country_id.l10n_ec_code_ats
