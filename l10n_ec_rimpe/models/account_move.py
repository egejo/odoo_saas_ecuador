# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_rimpe_retention_code(self, partner):
        """
        Returns the correct retention code based on RIMPE type.

        332: Negocio Popular (0%)
        343: Emprendedor (1%)

        NOTA: hasta el 2026-07-09 este metodo devolvia "332B"/"343A" -- bug
        real, esos codigos no corresponden a RIMPE en absoluto (332B es en
        realidad "Compra de bienes inmuebles" y 343A "Energia Electrica",
        ambos con 2%). Confirmado contra la Resolucion NAC-DGERCGC26-00000009
        y la hoja "Retenciones Marzo 2026" del SRI, ya auditado y corregido
        en el catalogo `l10n_ec.withholding.tax` el 2026-07-08 (ver
        retention_codes_2026.xml) -- este helper nunca se habia actualizado
        en consecuencia porque no estaba conectado a nada real (ver
        _default_rimpe_retention_line en retention_wizard.py de este mismo
        modulo, que ahora si lo usa).
        """
        if partner.l10n_ec_rimpe_type == "popular_business":
            return "332"
        elif partner.l10n_ec_rimpe_type == "entrepreneur":
            return "343"
        return None
