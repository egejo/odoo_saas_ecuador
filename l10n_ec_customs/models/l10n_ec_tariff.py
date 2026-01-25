from odoo import models, fields


class L10nEcTariffHeading(models.Model):
    _name = "l10n_ec.tariff.heading"
    _description = "Tariff Headings (Partida Arancelaria)"

    name = fields.Char("Tariff Code", required=True, index=True)  # e.g. 8471.30.00.00
    description = fields.Char("Description")

    ad_valorem = fields.Float("Ad Valorem (%)", default=0.0)
    specific_duty = fields.Float("Specific Duty ($/Unit)", default=0.0)
    fodinfa = fields.Float("FODINFA (%)", default=0.5)

    active = fields.Boolean(default=True)
