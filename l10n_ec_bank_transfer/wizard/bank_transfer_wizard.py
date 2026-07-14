# -*- coding: utf-8 -*-
import base64
from odoo import models, fields
from odoo.exceptions import UserError


class L10nEcBankTransferWizard(models.TransientModel):
    _name = "l10n_ec.bank.transfer.wizard"
    _description = "Generate Bank Cash Management Files"

    bank_id = fields.Selection(
        [
            ("pichincha", "Banco Pichincha (Cash Management)"),
            ("guayaquil", "Banco Guayaquil (Multicash)"),
        ],
        string="Target Bank",
        required=True,
        default="pichincha",
    )

    payment_date = fields.Date(
        string="Payment Date", default=fields.Date.context_today, required=True
    )
    description = fields.Char(string="Batch Description", default="NOMINA MENSUAL")

    # We will process Payslips marked as 'done' but not yet paid?
    # Or just select a Payslip Batch? For MVP simplicity, we select a list of payslips.
    payslip_ids = fields.Many2many("l10n_ec.payslip", string="Payslips to Pay")

    # Output
    filename = fields.Char()
    file_data = fields.Binary()

    def _check_payslips_have_bank_account(self):
        missing = self.payslip_ids.filtered(
            lambda s: s.net_wage > 0 and not s.employee_id.bank_account_id
        )
        if missing:
            raise UserError(
                "Los siguientes empleados no tienen cuenta bancaria "
                "configurada, no se puede generar el archivo de pago sin "
                "arriesgar una transferencia a una cuenta invalida: %s"
                % ", ".join(missing.mapped("employee_id.name"))
            )

    def action_generate(self):
        """
        Generates the TXT file based on selected Bank.
        """
        self.ensure_one()
        self._check_payslips_have_bank_account()
        if self.bank_id == "pichincha":
            self._generate_pichincha_txt()
        elif self.bank_id == "guayaquil":
            self._generate_guayaquil_txt()

        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_ec.bank.transfer.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def _amount_to_cents_str(self, amount):
        """Pichincha exige el VALOR sin coma ni punto decimal -- los ultimos
        2 digitos son los centavos (confirmado contra la ayuda oficial de
        Pichincha Cash Management: "enter the number without commas or
        decimal points, as the system will automatically take the last two
        values as decimals"). Un simple '{:.2f}' (con punto) es un formato
        distinto al que el banco realmente espera."""
        return str(int(round(amount * 100)))

    def _generate_pichincha_txt(self):
        """
        Generates Banco Pichincha 'Cash Management' Header/Detail structure.
        Structure (Simplified Standard):
        HEADER: PA (Pago), RUC, Date, Reference
        DETAIL: TipoID, ID, Nombre, Valor(sin decimales), TipoCta, NumCta, Ref

        OJO: solo el formato de los campos individuales (VALOR sin punto,
        TIPO ID de 1 letra, TIPO CTA AHO/CTE) esta confirmado contra la
        ayuda oficial publicada de Pichincha -- el layout completo de
        header/detalle/delimitador exacto NO se verifico contra el
        instructivo PDF completo (viene escaneado, sin texto extraible en
        este entorno). Validar contra un archivo de prueba real del banco
        antes de usar esto para un pago real.
        """
        lines = []

        # 1. Header
        # PA | RUC_EMPRESA | USD | DATE | BATCH_REF
        company = self.env.company
        header = f"PA\t{company.vat}\tUSD\t{self.payment_date.strftime('%Y%m%d')}\t{self.description}"
        lines.append(header)

        # 2. Details
        total_cents = 0
        payslips_included = 0
        for slip in self.payslip_ids:
            if slip.net_wage <= 0:
                continue

            emp = slip.employee_id
            # _check_payslips_have_bank_account ya garantizo que toda
            # planilla con net_wage > 0 que llega aqui tiene bank_account_id.
            bank_acc = emp.bank_account_id
            acc_type = "CTE" if bank_acc.l10n_ec_account_type == "corriente" else "AHO"
            acc_num = bank_acc.acc_number
            id_type = emp.l10n_ec_bank_id_type or "C"

            amount_cents_str = self._amount_to_cents_str(slip.net_wage)

            # Format: REF \t TIPO_ID \t ID \t BENEFICIARY \t VALOR \t ACC_TYPE \t ACC_NUM
            line = (
                f"{slip.name}\t{id_type}\t{emp.identification_id}\t{emp.name}\t"
                f"{amount_cents_str}\t{acc_type}\t{acc_num}"
            )
            lines.append(line)
            total_cents += int(round(slip.net_wage * 100))
            payslips_included += 1

        # 3. Footer/Control (Optional in some formats, but good practice)
        # TOT | NUM_RECORDS | TOTAL_AMOUNT (mismo formato sin punto que el detalle)
        footer = f"TOT\t{payslips_included}\t{total_cents}"
        lines.append(footer)

        content = "\n".join(lines)

        self.filename = f"PICHINCHA_NOMINA_{self.payment_date}.txt"
        self.file_data = base64.b64encode(content.encode("utf-8"))

    def _generate_guayaquil_txt(self):
        """
        Genera el archivo Multicash de Banco Guayaquil.

        OJO: igual que Pichincha, solo se confirmaron algunos elementos
        contra la ayuda oficial publicada por el banco (convencion de
        nombre de archivo PAGOS_MULTICASH_AAAAMMDD_SS.TXT; que Referencia
        y Codigo/beneficiario son obligatorios; que para acreditar en
        cuenta se necesita banco/tipo/numero de cuenta) -- el layout
        completo de columnas/delimitador exacto NO esta verificado contra
        el instructivo completo. Validar con el banco antes de un envio
        real.
        """
        lines = []
        for slip in self.payslip_ids:
            if slip.net_wage <= 0:
                continue

            emp = slip.employee_id
            # _check_payslips_have_bank_account ya garantizo que toda
            # planilla con net_wage > 0 que llega aqui tiene bank_account_id.
            bank_acc = emp.bank_account_id
            acc_type = "CTE" if bank_acc.l10n_ec_account_type == "corriente" else "AHO"
            acc_num = bank_acc.acc_number
            bank_name = bank_acc.bank_id.name if bank_acc.bank_id else ""
            id_type = emp.l10n_ec_bank_id_type or "C"

            amount_str = "{:.2f}".format(slip.net_wage)
            line = (
                f"{slip.name};{id_type};{emp.identification_id};{emp.name};"
                f"{amount_str};{bank_name};{acc_type};{acc_num}"
            )
            lines.append(line)

        content = "\n".join(lines)

        seq = "01"
        self.filename = f"PAGOS_MULTICASH_{self.payment_date.strftime('%Y%m%d')}_{seq}.TXT"
        self.file_data = base64.b64encode(content.encode("utf-8"))
