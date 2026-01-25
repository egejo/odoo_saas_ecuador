# -*- coding: utf-8 -*-
import base64
import io
import csv
from odoo import models, fields, _


class L10nEcLoanImportWizard(models.TransientModel):
    _name = "l10n_ec.loan.import.wizard"
    _description = "Import IESS Loan Planilla"

    file_data = fields.Binary("File (CSV/TXT)", required=True)
    filename = fields.Char("Filename")
    delimiter = fields.Char("Delimiter", default=";")

    def action_import(self):
        """
        Parses IESS format.
        Expected columns (example): Cedula, Nombre, Tipo, Monto, Cuota
        Note: Exact IESS format varies, implementing generic structure for MVP.
        """
        self.ensure_one()
        decoded_data = base64.b64decode(self.file_data).decode("utf-8")
        f = io.StringIO(decoded_data)
        reader = csv.DictReader(f, delimiter=self.delimiter)

        loans_created = 0

        for row in reader:
            cedula = row.get("cedula", "").strip()
            amount_str = row.get("valor", "0").replace(",", ".")

            if not cedula:
                continue

            employee = self.env["hr.employee"].search(
                [("identification_id", "=", cedula)], limit=1
            )
            if not employee:
                # Log error or skip
                continue

            amount = float(amount_str)

            # Create a simple loan entry for this month's deduction (Common IESS practice is monthly file)
            # We create a 1-installment active loan for this deduction
            loan = self.env["l10n_ec.loan"].create(
                {
                    "name": f"IESS Import - {fields.Date.today()}",
                    "employee_id": employee.id,
                    "loan_type": "iess_qui",  # Defaulting for import
                    "amount_total": amount,
                    "date_start": fields.Date.today(),
                    "state": "active",
                }
            )

            self.env["l10n_ec.loan.line"].create(
                {"loan_id": loan.id, "date_due": fields.Date.today(), "amount": amount}
            )

            loans_created += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Import Successful"),
                "message": _("%s loans imported from IESS file.") % loans_created,
                "type": "success",
            },
        }
