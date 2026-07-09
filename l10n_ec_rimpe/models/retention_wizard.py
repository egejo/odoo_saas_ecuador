# -*- coding: utf-8 -*-
from odoo import api, models


class RetentionWizard(models.TransientModel):
    _inherit = "l10n_ec.retention.wizard"

    @api.model
    def default_get(self, fields_list):
        """
        Si el proveedor de la factura esta clasificado como RIMPE (Negocio
        Popular o Emprendedor), preselecciona el codigo de retencion renta
        correcto (332/343) en vez de dejarlo en blanco -- el wizard base
        (l10n_ec_withholding) no lo hace porque en el caso general "no se
        puede adivinar de forma confiable" el codigo, pero para un
        proveedor RIMPE si se puede: el codigo depende unicamente de su
        clasificacion, no del tipo de bien/servicio comprado.
        """
        res = super().default_get(fields_list)
        invoice_id = res.get("invoice_id")
        if not invoice_id:
            return res

        invoice = self.env["account.move"].browse(invoice_id)
        code = invoice._get_rimpe_retention_code(invoice.partner_id)
        if not code:
            return res

        tax = self.env["l10n_ec.withholding.tax"].search(
            [("type", "=", "renta"), ("code", "=", code)], limit=1
        )
        if not tax:
            return res

        for line in res.get("line_ids", []):
            if line[2].get("tax_type") == "renta" and not line[2].get("tax_id"):
                line[2]["tax_id"] = tax.id

        return res
