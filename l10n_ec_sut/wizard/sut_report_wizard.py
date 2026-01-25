# -*- coding: utf-8 -*-
import base64
from odoo import models, fields, api, _

class L10nEcSutReportWizard(models.TransientModel):
    _name = 'l10n_ec.sut.report.wizard'
    _description = 'MDT SUT Report Generator'

    report_type = fields.Selection([
        ('13th', 'Décimo Tercero'),
        ('14th', 'Décimo Cuarto'),
        ('utilidades', 'Utilidades')
    ], string='Report Type', required=True)

    date_start = fields.Date("Start Date", required=True)
    date_end = fields.Date("End Date", required=True)

    # Generated File
    filename = fields.Char("Filename")
    file_data = fields.Binary("Report File")

    def action_generate(self):
        self.ensure_one()

        # 1. Fetch relevant Payslips
        domain = [
            ('state', '=', 'done'),
            ('date_end', '>=', self.date_start),
            ('date_start', '<=', self.date_end)
        ]
        payslips = self.env['l10n_ec.payslip'].search(domain)

        content = ""

        # 2. Generate Content based on Type (Simplified Logic for MVP)
        # SUT usually requires: Cedula, Names, Days Worked, Earnings, etc.
        # We will use a standard CSV structure for "Carga Batch"

        if self.report_type == '13th':
            # Header
            content += "Cedula,Nombres,Dias_Trabajados,Total_Ganado,Valor_Decimo\n"
            for p in payslips:
                # Aggregate Logic needed in real life usually by employee, but here listing payslips
                # For 13th, usually we need the accumulated amount.
                # Assuming this wizard runs on a "13th Payment" batch or aggregates:
                content += f"{p.employee_id.identification_id},{p.employee_id.name},{p.days_worked},{p.total_income},{p.thirteenth}\n"

        elif self.report_type == '14th':
            content += "Cedula,Nombres,Region,Dias_Trabajados,Valor_Decimo\n"
            for p in payslips:
                content += f"{p.employee_id.identification_id},{p.employee_id.name},Sierra,{p.days_worked},{p.fourteenth}\n"

        elif self.report_type == 'utilidades':
             # Placeholder for Utilidades logic (Phase 6?)
             content += "Cedula,Nombres,Cargas,Dias,Valor_Utilidad\n"
             # No utilidades calculation in Payslip yet, so leaving blank or mock
             content += "REPORT_NOT_IMPLEMENTED_YET\n"

        # 3. Save
        self.filename = f"SUT_{self.report_type}_{self.date_end}.txt"
        self.file_data = base64.b64encode(content.encode('utf-8'))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_ec.sut.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
