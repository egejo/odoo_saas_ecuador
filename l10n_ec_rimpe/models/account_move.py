# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_rimpe_retention_code(self, partner):
        """
        Returns the correct retention code based on RIMPE type.
        332B: Negocio Popular (0%)
        343A: Emprendedor (1%)
        """
        if partner.l10n_ec_rimpe_type == "popular_business":
            return "332B"
        elif partner.l10n_ec_rimpe_type == "entrepreneur":
            return "343A"
        return None

    # Logic to override retention application would go here
    # For now, we define the helper that will be used by the withholding module integration
