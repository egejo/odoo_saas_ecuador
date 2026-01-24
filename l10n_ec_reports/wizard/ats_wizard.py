# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import base64
from datetime import datetime
from odoo.exceptions import UserError

class L10nEcAtsWizard(models.TransientModel):
    _name = 'l10n_ec.ats.wizard'
    _description = 'Anexo Transaccional Simplificado (ATS) Wizard'

    date_month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True, default=lambda self: datetime.now().strftime('%m'))

    date_year = fields.Char(string='Year', required=True, default=lambda self: datetime.now().strftime('%Y'))
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    # Result
    xml_data = fields.Binary('ATS XML', readonly=True)
    xml_filename = fields.Char(string='Filename', readonly=True)

    def action_generate_ats(self):
        self.ensure_one()
        xml_content = self.generate_xml()
        self.xml_data = base64.b64encode(xml_content)
        self.xml_filename = f"ATS_{self.date_month}_{self.date_year}_{self.company_id.vat}.xml"

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_ec.ats.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def generate_xml(self):
        """
        Real implementation of ATS generation.
        Aggregates Purchases, Sales, and Retentions for the selected period.
        """
        # 1. Date Range
        try:
            date_start = datetime.strptime(f"{self.date_year}-{self.date_month}-01", "%Y-%m-%d").date()
            if self.date_month == '12':
                date_end = datetime.strptime(f"{int(self.date_year)+1}-01-01", "%Y-%m-%d").date()
            else:
                date_end = datetime.strptime(f"{self.date_year}-{int(self.date_month)+1:02d}-01", "%Y-%m-%d").date()
        except ValueError:
            raise UserError(_("Invalid Date Configuration"))

        # 2. Purchases (Compras)
        # Fetch posted Invoices
        domain_in = [
            ('move_type', '=', 'in_invoice'),
            ('invoice_date', '>=', date_start),
            ('invoice_date', '<', date_end),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id)
        ]
        in_invoices = self.env['account.move'].search(domain_in)

        purchases_data = []

        for inv in in_invoices:
            # Identifier Type Map
            if inv.partner_id.l10n_ec_identifier_type == 'ruc':
                tpId = '01'
            elif inv.partner_id.l10n_ec_identifier_type == 'cedula':
                tpId = '02'
            else:
                tpId = '03' # Pasaporte

            # Parse Document Number (001-001-123456789)
            parts = inv.l10n_latam_document_number.split('-') if inv.l10n_latam_document_number else []
            if len(parts) == 3:
                estab, pto, sec = parts
            else:
                estab, pto, sec = '001', '001', '999999999'

            # Totals
            base_0 = sum(l.price_subtotal for l in inv.invoice_line_ids if not l.tax_ids)
            base_15 = sum(l.price_subtotal for l in inv.invoice_line_ids if l.tax_ids) # Simplified
            monto_iva = inv.amount_tax

            # Retentions (AIR)
            # Find related retentions
            # We assume retention is linked via invoice_id on account.retention
            retentions_recs = self.env['account.retention'].search([('invoice_id', '=', inv.id), ('state', '=', 'posted')])
            air_data = []
            ret_info = {'estabRet': '000', 'ptoEmiRet': '000', 'secRet': '0', 'autRet': '0', 'fechaEmiRet': ''}

            if retentions_recs:
                main_ret = retentions_recs[0] # Take first valid retention
                ret_parts = main_ret.name.split('-') if main_ret.name else []
                if len(ret_parts) == 3:
                     ret_info['estabRet'] = ret_parts[0]
                     ret_info['ptoEmiRet'] = ret_parts[1]
                     ret_info['secRet'] = ret_parts[2]
                ret_info['autRet'] = main_ret.l10n_ec_sri_access_key or '0000000000'
                ret_info['fechaEmiRet'] = main_ret.date.strftime('%d/%m/%Y')

                for line in main_ret.retention_line_ids:
                    if line.tax_type == '1': # Renta only for AIR
                        air_data.append({
                            'code': line.tax_code,
                            'base': line.base,
                            'percent': line.percentage,
                            'val': line.amount
                        })

            purchases_data.append({
                'sustento': inv.l10n_ec_sustento_code or '01',
                'tpIdProv': tpId,
                'idProv': inv.partner_id.vat,
                'tipoComprobante': inv.l10n_latam_document_type_id.code or '01',
                'fechaRegistro': inv.date.strftime('%d/%m/%Y'),
                'estab': estab,
                'ptoEmi': pto,
                'secuencial': sec,
                'fechaEmision': inv.invoice_date.strftime('%d/%m/%Y'),
                'autorizacion': inv.l10n_ec_authorization or '9999999999',
                'baseNoGraIva': 0.0,
                'baseImponible': base_0,
                'baseImpGrav': base_15,
                'montoIva': monto_iva,
                'retentions': air_data,
                **ret_info
            })

        # 3. Sales (Ventas)
        # Aggregated by Partner
        domain_out = [
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', date_start),
            ('invoice_date', '<', date_end),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id)
        ]
        out_invoices = self.env['account.move'].read_group(
            domain=domain_out,
            fields=['partner_id', 'amount_untaxed', 'amount_tax', 'l10n_latam_document_type_id'],
            groupby=['partner_id', 'l10n_latam_document_type_id']
        )

        sales_data = []
        total_sales_period = 0.0

        for grp in out_invoices:
            pid = grp['partner_id'][0]
            partner = self.env['res.partner'].browse(pid)

            # Identifier
            if partner.l10n_ec_identifier_type == 'ruc':
                tpId = '04'
            elif partner.l10n_ec_identifier_type == 'cedula':
                tpId = '05'
            else:
                tpId = '06'

            doctype = self.env['l10n_latam.document.type'].browse(grp['l10n_latam_document_type_id'][0])

            sales_data.append({
                'tpIdCliente': tpId,
                'idCliente': partner.vat,
                'tipoComprobante': doctype.code or '18',
                'count': grp['partner_id_count'],
                'baseImpGrav': grp['amount_untaxed'], # Simplified, assumes all taxed
                'montoIva': grp['amount_tax'],
                'baseNoGraIva': 0.0,
                'baseImponible': 0.0
            })
            total_sales_period += grp['amount_untaxed']

        # 4. Render
        values = {
            'wizard': self,
            'company': self.company_id,
            'purchases': purchases_data,
            'sales': sales_data,
            'cancelled': self._get_cancelled_documents(date_start, date_end),
            'total_sales': total_sales_period,
            'format_float': lambda x, p: ("%." + str(p) + "f") % x,
        }

        xml_content = self.env['ir.qweb']._render('l10n_ec_reports.l10n_ec_ats_xml', values)
        return xml_content.encode('utf-8')

    def _get_cancelled_documents(self, date_start, date_end):
        """Fetch cancelled/voided invoices for the ATS period."""
        domain = [
            ('move_type', 'in', ['out_invoice', 'in_invoice']),
            ('invoice_date', '>=', date_start),
            ('invoice_date', '<', date_end),
            ('state', '=', 'cancel'),
            ('company_id', '=', self.company_id.id)
        ]
        cancelled_moves = self.env['account.move'].search(domain)

        cancelled_data = []
        for inv in cancelled_moves:
            doc_type = inv.l10n_latam_document_type_id.code or '01'
            parts = inv.l10n_latam_document_number.split('-') if inv.l10n_latam_document_number else []
            if len(parts) == 3:
                estab, pto, sec = parts
            else:
                estab, pto, sec = '001', '001', '999999999'

            cancelled_data.append({
                'tipoComprobante': doc_type,
                'estab': estab,
                'ptoEmi': pto,
                'secuencialIni': sec,
                'secuencialFin': sec,
                'autorizacion': inv.l10n_ec_sri_access_key or '',
            })

        return cancelled_data

