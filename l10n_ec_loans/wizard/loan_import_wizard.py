# -*- coding: utf-8 -*-
import base64
import io
import csv
import unicodedata
from odoo import models, fields, api, _
from odoo.exceptions import UserError


def _normalize_key(key):
    """Lowercase + strip accents/whitespace so header matching survives the
    real-world casing/accent variants IESS files show up with (Cedula,
    CEDULA, Cédula...) instead of only the exact literal "cedula"."""
    if key is None:
        return ""
    key = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode("ascii")
    return key.strip().lower()


# Valores reales encontrados en archivos IESS para el tipo de prestamo,
# mapeados a la selection de l10n_ec.loan. Cualquier valor no reconocido
# (o columna ausente) cae a quirografario, el tipo mas comun.
_TIPO_MAP = {
    "quirografario": "iess_qui",
    "q": "iess_qui",
    "hipotecario": "iess_hip",
    "h": "iess_hip",
}


class L10nEcLoanImportWizard(models.TransientModel):
    _name = "l10n_ec.loan.import.wizard"
    _description = "Import IESS Loan Planilla"

    file_data = fields.Binary("File (CSV/TXT)", required=True)
    filename = fields.Char("Filename")
    delimiter = fields.Char("Delimiter", default=";")
    date_due = fields.Date(
        "Fecha de descuento",
        default=fields.Date.context_today,
        required=True,
        help="Periodo/fecha en que se debe deducir esta planilla -- debe "
        "caer dentro del date_start/date_end del rol de pagos donde se "
        "quiere ver el descuento. No asumir que coincide con la fecha en "
        "que se importa el archivo (p.ej. si la planilla de julio se "
        "importa recien en agosto).",
    )

    def _parse_amount(self, raw):
        """Convierte un monto de texto tolerando tanto el formato con coma
        decimal (1.234,56 -- LATAM) como con punto decimal (1234.56 -- el
        que usa el propio archivo ASCII que exige IESS para empleadores).
        Un simple .replace(',', '.') revienta con separador de miles."""
        raw = (raw or "").strip()
        if not raw:
            return 0.0
        if "," in raw and "." in raw:
            # El separador que aparece de ultimo es el decimal real.
            if raw.rfind(",") > raw.rfind("."):
                raw = raw.replace(".", "").replace(",", ".")
            else:
                raw = raw.replace(",", "")
        elif "," in raw:
            raw = raw.replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            raise UserError(
                _("Valor de monto invalido en el archivo: '%s'") % raw
            )

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

        if reader.fieldnames:
            normalized_fieldnames = {_normalize_key(k) for k in reader.fieldnames}
            if "cedula" not in normalized_fieldnames:
                raise UserError(
                    _(
                        "El archivo no tiene una columna 'Cedula' reconocible "
                        "(columnas encontradas: %s). Revisar el delimitador o "
                        "el archivo."
                    )
                    % ", ".join(reader.fieldnames)
                )

        loans_created = 0
        loans_skipped_duplicate = 0
        employees_not_found = []

        for row in reader:
            normalized_row = {_normalize_key(k): v for k, v in row.items()}

            cedula = (normalized_row.get("cedula") or "").strip()
            amount_str = normalized_row.get("valor") or normalized_row.get(
                "monto"
            ) or normalized_row.get("cuota", "0")
            tipo_raw = _normalize_key(normalized_row.get("tipo"))

            if not cedula:
                continue

            employee = self.env["hr.employee"].search(
                [("identification_id", "=", cedula)], limit=1
            )
            if not employee:
                employees_not_found.append(cedula)
                continue

            amount = self._parse_amount(amount_str)
            loan_type = _TIPO_MAP.get(tipo_raw, "iess_qui")

            # Evitar duplicar el descuento si el mismo archivo (u otro que
            # cubra el mismo periodo) ya se importo antes para este
            # empleado -- antes no habia ningun chequeo y reimportar el
            # mismo archivo por error duplicaba la deduccion.
            existing = self.env["l10n_ec.loan.line"].search(
                [
                    ("loan_id.employee_id", "=", employee.id),
                    ("date_due", "=", self.date_due),
                ],
                limit=1,
            )
            if existing:
                loans_skipped_duplicate += 1
                continue

            # Create a simple loan entry for this month's deduction (Common IESS practice is monthly file)
            # We create a 1-installment active loan for this deduction
            loan = self.env["l10n_ec.loan"].create(
                {
                    "name": f"IESS Import - {self.date_due}",
                    "employee_id": employee.id,
                    "loan_type": loan_type,
                    "amount_total": amount,
                    "date_start": self.date_due,
                    "state": "active",
                }
            )

            self.env["l10n_ec.loan.line"].create(
                {"loan_id": loan.id, "date_due": self.date_due, "amount": amount}
            )

            loans_created += 1

        message_parts = [_("%s préstamos importados desde el archivo del IESS.") % loans_created]
        if loans_skipped_duplicate:
            message_parts.append(
                _("%s omitidos por ya existir un descuento para esa fecha.")
                % loans_skipped_duplicate
            )
        if employees_not_found:
            message_parts.append(
                _("Cédulas no encontradas: %s.") % ", ".join(employees_not_found)
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Import Successful"),
                "message": " ".join(message_parts),
                "type": "success" if not employees_not_found else "warning",
            },
        }
