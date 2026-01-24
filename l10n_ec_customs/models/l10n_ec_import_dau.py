from odoo import models, fields, api

class L10nEcImportDau(models.Model):
    _name = 'l10n_ec.import.dau'
    _description = 'Declaración Aduanera Única (Import)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("DAU Number", required=True, tracking=True)
    date = fields.Date("Declaration Date", default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string="Customs Broker/Supplier")

    picking_id = fields.Many2one('stock.picking', string="Related Receipt")
    invoice_id = fields.Many2one('account.move', string="Commercial Invoice")

    # Values
    fob_value = fields.Float("FOB Value", compute='_compute_fob_total', store=True, tracking=True)
    freight = fields.Float("Freight")
    insurance = fields.Float("Insurance")
    cif_value = fields.Float("CIF Value", compute='_compute_cif', store=True)

    # Taxes
    total_ad_valorem = fields.Float("Total Ad Valorem", compute='_compute_taxes', store=True)
    total_fodinfa = fields.Float("Total FODINFA", compute='_compute_taxes', store=True)
    total_iva = fields.Float("Total IVA Importación", compute='_compute_taxes', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('done', 'Done')
    ], default='draft')

    line_ids = fields.One2many('l10n_ec.import.dau.line', 'dau_id', string="Lines")

    @api.depends('line_ids.valor_fob_line')
    def _compute_fob_total(self):
        for rec in self:
            rec.fob_value = sum(line.valor_fob_line for line in rec.line_ids)

    @api.depends('fob_value', 'freight', 'insurance')
    def _compute_cif(self):
        for rec in self:
            rec.cif_value = rec.fob_value + rec.freight + rec.insurance

    @api.depends('line_ids.ad_valorem_amount', 'cif_value')
    def _compute_taxes(self):
        for rec in self:
            # FODINFA and IVA from Parameters
            fodinfa_param = self.env['ir.config_parameter'].sudo().get_param('l10n_ec.fodinfa', '0.005')
            iva_param = self.env['ir.config_parameter'].sudo().get_param('l10n_ec.customs_iva', '0.15')

            try:
                fodinfa_rate = float(fodinfa_param)
                iva_rate = float(iva_param)
            except ValueError:
                fodinfa_rate = 0.005
                iva_rate = 0.15

            rec.total_ad_valorem = sum(line.ad_valorem_amount for line in rec.line_ids)
            rec.total_fodinfa = rec.cif_value * fodinfa_rate

            # Simplified IVA Base = CIF + AdValorem + Fodinfa
            base_iva = rec.cif_value + rec.total_ad_valorem + rec.total_fodinfa
            rec.total_iva = base_iva * iva_rate

    def action_calculate(self):
        for rec in self:
            rec._compute_cif()
            rec._compute_taxes()
        self.write({'state': 'calculated'})

class L10nEcImportDauLine(models.Model):
    _name = 'l10n_ec.import.dau.line'
    _description = 'DAU Line'

    dau_id = fields.Many2one('l10n_ec.import.dau', required=True)
    product_id = fields.Many2one('product.product', string="Product")
    tariff_id = fields.Many2one('l10n_ec.tariff.heading', string="Tariff Heading")

    valor_fob_line = fields.Float("FOB (Line)")
    cif_line = fields.Float("CIF (Line)", compute='_compute_cif_line', store=True)

    ad_valorem_amount = fields.Float("Ad Valorem", compute='_compute_duties', store=True)

    @api.depends('dau_id.cif_value', 'dau_id.fob_value', 'valor_fob_line')
    def _compute_cif_line(self):
        for rec in self:
            header = rec.dau_id
            if header.fob_value and header.fob_value > 0:
                # Ratio: Header CIF / Header FOB
                ratio = header.cif_value / header.fob_value
                rec.cif_line = rec.valor_fob_line * ratio
            else:
                # Fallback if no FOB (shouldn't happen if lines exist)
                rec.cif_line = rec.valor_fob_line

    @api.depends('tariff_id', 'cif_line')
    def _compute_duties(self):
        for rec in self:
            if rec.tariff_id:
                # Ad Valorem applied to CIF Line
                rec.ad_valorem_amount = rec.cif_line * (rec.tariff_id.ad_valorem / 100.0)
            else:
                rec.ad_valorem_amount = 0.0
