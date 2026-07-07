# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RetentionWizard(models.TransientModel):
    _name = "l10n_ec.retention.wizard"
    _description = "Wizard to Create Withholding Document"

    invoice_id = fields.Many2one("account.move", string="Invoice", required=True)
    partner_id = fields.Many2one(related="invoice_id.partner_id", string="Vendor")
    date = fields.Date(string="Date", default=fields.Date.context_today)

    line_ids = fields.One2many(
        "l10n_ec.retention.wizard.line", "wizard_id", string="Withholding Lines"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(RetentionWizard, self).default_get(fields_list)
        if (
            "active_id" in self.env.context
            and self.env.context.get("active_model") == "account.move"
        ):
            invoice = self.env["account.move"].browse(self.env.context["active_id"])
            res["invoice_id"] = invoice.id

            lines = []
            # Auto-calculation logic
            # We look for Taxes on the Invoice Lines that are "Retentions"
            # Since we don't have strict Tax Group mapping in this scaffold yet,
            # we will create lines based on the invoice lines tax calculations if they appear to be retentions
            # OR, more robustly for a Wizard: We allow the user to select the code and we apply it to the base.

            # Strategy: Pre-fill base amounts from invoice totals to save typing
            # Separate by VAT and Income Tax bases if possible.

            # Simple approach: Create one line for Income Tax (Renta) and one for VAT (IVA) if applicable.
            # Base Imponible Renta = Amount Untaxed
            # Base Imponible IVA = Amount Tax (only if Retaining IVA)

            # Sugerencia de bases (Renta = subtotal sin impuestos; IVA =
            # valor del IVA de la factura, ya que la retencion de IVA se
            # calcula como % sobre el IVA facturado, no sobre el
            # subtotal). El codigo de retencion (tax_id) exacto depende
            # del tipo de bien/servicio -- no se puede adivinar de forma
            # confiable, asi que se deja en blanco para que el usuario lo
            # elija; solo se preselecciona el tipo de impuesto y la base
            # para ahorrar tipeo.
            lines.append(
                (
                    0,
                    0,
                    {
                        "tax_type": "renta",
                        "base": invoice.amount_untaxed,
                    },
                )
            )

            total_vat = sum(
                line.price_total - line.price_subtotal
                for line in invoice.invoice_line_ids
            )
            if total_vat > 0:
                lines.append(
                    (
                        0,
                        0,
                        {
                            "tax_type": "iva",
                            "base": total_vat,
                        },
                    )
                )

            res["line_ids"] = lines

        return res

    def action_create_retention(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Please add at least one withholding line."))

        retention_vals = {
            "invoice_id": self.invoice_id.id,
            "partner_id": self.partner_id.id,
            "date": self.date,
            "company_id": self.invoice_id.company_id.id,
            "l10n_ec_sri_status": "draft",
            "retention_line_ids": [],
        }

        for line in self.line_ids:
            # tax_code/percentage son related (derivados de tax_id) y no
            # hace falta pasarlos aqui. "amount" si se pasa explicito:
            # es un campo computado con store=True que depende de un
            # related (percentage), y al crear account.retention con sus
            # retention_line_ids anidados en un solo create() -- igual que
            # aqui -- Odoo puede intentar el INSERT antes de resolver esa
            # cadena de related+compute, violando el NOT NULL de "amount".
            # Calcularlo aqui de una vez evita depender de ese orden.
            retention_vals["retention_line_ids"].append(
                (
                    0,
                    0,
                    {
                        "tax_type": line.tax_type,
                        "tax_id": line.tax_id.id,
                        "base": line.base,
                        "amount": line.base * (line.tax_id.percentage / 100.0),
                    },
                )
            )

        retention = self.env["account.retention"].create(retention_vals)

        # Link back to invoice for smart button (if we add one) or just return view
        return {
            "name": _("Withholding"),
            "type": "ir.actions.act_window",
            "res_model": "account.retention",
            "res_id": retention.id,
            "view_mode": "form",
            "target": "current",
        }


class RetentionWizardLine(models.TransientModel):
    _name = "l10n_ec.retention.wizard.line"
    _description = "Retention Wizard Line"

    wizard_id = fields.Many2one("l10n_ec.retention.wizard", required=True)
    # Mismo vocabulario que l10n_ec.withholding.tax.type y
    # account.retention.line.tax_type (ver comentario ahi): antes usaba
    # "1"/"2"/"6" mientras tax_id.type usa "renta"/"iva"/"isd", asi que el
    # dominio de abajo nunca encontraba resultados.
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
    tax_code = fields.Char(related="tax_id.code", string="Código", readonly=True)
    percentage = fields.Float(
        related="tax_id.percentage", string="Porcentaje %", readonly=True
    )
    base = fields.Monetary(string="Base Imponible", required=True)
    amount = fields.Monetary(string="Valor Retenido", compute="_compute_amount")
    currency_id = fields.Many2one(related="wizard_id.invoice_id.currency_id")

    @api.depends("base", "percentage")
    def _compute_amount(self):
        for line in self:
            line.amount = line.base * (line.percentage / 100.0)
