# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    # Requerido por el layout real de Pichincha Cash Management (TIPO CTA:
    # AHO=ahorros, CTE=corriente) -- Odoo core no distingue tipo de cuenta,
    # solo numero/banco/titular.
    l10n_ec_account_type = fields.Selection(
        [("ahorros", "Ahorros"), ("corriente", "Corriente")],
        string="Tipo de Cuenta (EC)",
        default="ahorros",
        help="Tipo de cuenta para archivos de pago masivo bancario "
        "(Pichincha Cash Management: AHO/CTE). Por defecto Ahorros, el "
        "caso mas comun para cuentas de empleados.",
    )


class HrEmployeeBank(models.Model):
    _inherit = "hr.employee"

    # Requerido por el layout real de Pichincha Cash Management (TIPO ID:
    # solo el primer caracter, C=cedula/R=RUC/P=pasaporte). hr.employee no
    # tiene ningun campo de tipo de identificacion (identification_id es un
    # Char libre) -- se agrega aqui, no en l10n_ec_base, porque es
    # especifico del layout de este banco, no de EDI/retenciones.
    l10n_ec_bank_id_type = fields.Selection(
        [("C", "Cédula"), ("R", "RUC"), ("P", "Pasaporte")],
        string="Tipo ID (Transferencias Bancarias)",
        default="C",
        help="Tipo de identificación para archivos de pago masivo "
        "bancario. La inmensa mayoría de empleados en Ecuador tiene "
        "cédula -- cambiar solo para el caso raro de un extranjero con "
        "pasaporte.",
    )
