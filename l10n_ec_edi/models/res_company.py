# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_ec_sri_environment = fields.Selection(
        [("test", "Test"), ("production", "Production")],
        string="SRI Environment",
        default="test",
    )

    # Linked to the robust Certificate model instead of simple binary
    l10n_ec_certificate_id = fields.Many2one(
        "l10n_ec.certificate",
        string="SRI Electronic Signature",
        domain=[("state", "=", "active")],
        help="Select the active P12 certificate for signing.",
    )

    l10n_ec_withhold_agent = fields.Boolean("Withholding Agent")
    l10n_ec_withhold_resolution = fields.Char("Resolution Number")
    l10n_ec_special_resolution = fields.Char("Special Contributor Resolution")
    l10n_ec_forced_accounting = fields.Boolean("Forced to keep Accounting")
    l10n_ec_commercial_name = fields.Char("Commercial Name")

    # Regimen tributario de la propia compañía (no confundir con
    # l10n_ec_rimpe_type de res.partner en l10n_ec_rimpe, que clasifica al
    # CONTACTO -- proveedor o cliente -- para efecto de que codigo de
    # retencion aplicarle a el). Este campo es sobre la compañia emisora
    # misma: si Adrenasports estuviera registrada bajo RIMPE, el SRI exige
    # imprimir la leyenda "CONTRIBUYENTE REGIMEN RIMPE" en el XML y el RIDE
    # de cada comprobante que emite. Estructura verificada contra Enterprise
    # (l10n_ec_edi/models/res_company.py campo l10n_ec_regime, usado solo
    # como referencia -- Enterprise documenta explicitamente que este flag
    # "no afecta el calculo de retenciones", coincide con el diseño de este
    # fork donde las retenciones especiales RIMPE dependen del campo
    # separado en res.partner, no de este).
    l10n_ec_regime = fields.Selection(
        [("regular", "Régimen General"), ("rimpe", "Régimen RIMPE")],
        string="Régimen Tributario",
        default="regular",
        required=True,
        help="Si la compañía está registrada bajo el régimen RIMPE "
        "(Emprendedor o Negocio Popular), se agrega la leyenda "
        "'CONTRIBUYENTE RÉGIMEN RIMPE' en el XML y el RIDE de los "
        "comprobantes electrónicos que emite, como exige el SRI. No afecta "
        "el cálculo de retenciones que esta compañía aplica como agente "
        "retenedor (eso depende de la clasificación RIMPE de cada "
        "proveedor, un campo separado en su ficha de Contacto).",
    )

    # URLs
    l10n_ec_sri_reception_url = fields.Char(
        string="SRI Reception URL",
        default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl",
    )
    l10n_ec_sri_authorization_url = fields.Char(
        string="SRI Authorization URL",
        default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl",
    )
