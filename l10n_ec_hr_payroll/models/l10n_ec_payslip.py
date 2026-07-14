from odoo import models, fields, api


class L10nEcPayslip(models.Model):
    _name = "l10n_ec.payslip"
    _description = "Ecuadorian Payslip"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(readonly=True)  # e.g. "Cedula - Month/Year"
    employee_id = fields.Many2one("hr.employee", required=True)
    contract_id = fields.Many2one("hr.contract", required=True)

    # Guardado en la propia linea (no leido de employee_id.company_id al
    # vuelo) a proposito: un usuario de portal leyendo su propio payslip
    # dispara el prefetch por lotes de Odoo sobre hr.employee, y ese
    # prefetch puede arrastrar otros registros de hr.employee ya en cache
    # (de otros empleados, restringidos para "perfiles publicos") en la
    # misma consulta -- un solo campo bloqueado ahi revienta el lote
    # completo con AccessError, aunque el campo que de verdad se pidio
    # (company_id) no sea sensible. Bug real encontrado 2026-07-14
    # auditando el portal de empleado con un usuario de portal sintetico.
    company_id = fields.Many2one(
        "res.company", related="employee_id.company_id", store=True, readonly=True
    )
    # Mismo motivo que company_id de arriba -- el reporte PDF/portal no
    # debe volver a tocar hr.employee al momento de renderizar.
    employee_name = fields.Char(related="employee_id.name", store=True, readonly=True)
    # hr.employee.identification_id tiene groups="hr.group_hr_user" -- un
    # campo related hereda ese groups automaticamente salvo que se anule
    # explicitamente aqui. Es correcto que la cedula no sea visible para
    # cualquiera, pero un empleado viendo SU PROPIO rol de pagos (ya
    # restringido a el mismo por el ir.rule de l10n_ec_portal) debe poder
    # ver su propia cedula, igual que en cualquier rol de pagos impreso.
    employee_identification_id = fields.Char(
        related="employee_id.identification_id", store=True, readonly=True, groups=""
    )

    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)

    days_worked = fields.Float(default=30.0)

    # Earnings
    wage = fields.Float(
        "Base Wage", compute="_compute_wage", store=True, readonly=False
    )
    overtime_hours = fields.Float(
        "Overtime (50%) Hours",
        compute="_compute_overtime_from_attendance",
        store=True,
        readonly=False,
    )
    supplementary_hours = fields.Float(
        "Supplementary (100%) Hours",
        compute="_compute_overtime_from_attendance",
        store=True,
        readonly=False,
    )
    commission = fields.Float("Commissions")
    bonus = fields.Float("Bonuses")

    # Computations
    total_income = fields.Float("Total Income", compute="_compute_totals", store=True)

    # Deductions
    iess_personal = fields.Float(
        "IESS Personal (9.45%)", compute="_compute_iess", store=True
    )
    income_tax = fields.Float(
        "Impuesto Renta", compute="_compute_totals", store=True
    )
    advances = fields.Float("Salary Advances")

    # Employer Costs
    iess_employer = fields.Float(
        "IESS Patronal (11.15%)", compute="_compute_iess", store=True
    )

    # Benefits (Provisions)
    thirteenth = fields.Float("13th Salary", compute="_compute_benefits", store=True)
    fourteenth = fields.Float("14th Salary", compute="_compute_benefits", store=True)
    reserve_funds = fields.Float(
        "Reserve Funds", compute="_compute_benefits", store=True
    )

    net_wage = fields.Float("Net Wage", compute="_compute_totals", store=True)
    total_benefits_cash = fields.Float(
        "Benefits (Cash)", compute="_compute_benefits", store=True
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("verify", "Verification"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )

    @api.depends("contract_id")
    def _compute_wage(self):
        for rec in self:
            rec.wage = rec.contract_id.wage if rec.contract_id else 0.0

    @api.depends(
        "wage",
        "overtime_hours",
        "supplementary_hours",
        "commission",
        "bonus",
        "advances",
    )
    def _compute_totals(self):
        for rec in self:
            # Simple calc for now - assumes Wage is monthly
            ot_rate = (rec.wage / 240) * 1.5
            supp_rate = (rec.wage / 240) * 2.0

            ot_pay = rec.overtime_hours * ot_rate
            supp_pay = rec.supplementary_hours * supp_rate

            rec.total_income = rec.wage + ot_pay + supp_pay + rec.commission + rec.bonus
            # Income Tax Calculation (SRI 2026 Progressive)
            rec.income_tax = rec._compute_income_tax_2026(
                rec.total_income, rec.iess_personal
            )

            rec.net_wage = (
                (rec.total_income + rec.total_benefits_cash)
                - rec.iess_personal
                - rec.income_tax
                - rec.advances
            )

    @api.depends("employee_id", "date_start", "date_end")
    def _compute_overtime_from_attendance(self):
        """
        PacERP Killer: Auto-calculate overtime from Biometric/Kiosk data.
        Logic:
        1. Fetch Attendance records within Payslip Period.
        2. Sum hours worked.
        3. Compare vs Contract Hours (e.g. 160h).
        4. Split Excess:
           - Weekdays > 8h -> 50% (Supplementary)
           - Weekends -> 100% (Extraordinary)
        """
        for rec in self:
            attendances = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", rec.employee_id.id),
                    ("check_in", ">=", rec.date_start),
                    ("check_out", "<=", rec.date_end),
                ]
            )

            total_supp_50 = 0.0
            total_extra_100 = 0.0

            for att in attendances:
                if not att.check_out:
                    continue

                # Calculate Duration
                delta = att.check_out - att.check_in
                hours = delta.total_seconds() / 3600.0

                # Check Day of Week (0=Mon, 6=Sun)
                # Odoo Datetime is UTC, need conversion to local typically?
                # For MVP we assume server time matches or is handled.
                weekday = att.check_in.weekday()

                # Logic:
                # If Weekend (Sat/Sun) -> 100%
                if weekday >= 5:
                    total_extra_100 += hours
                else:
                    # Weekday -> Standard is 8h. Excess is 50%.
                    # Note: Night shift (25%) logic omitted for MVP speed, focusing on OT.
                    if hours > 8.0:
                        extra = hours - 8.0
                        total_supp_50 += extra

            # overtime_hours = 50% (Suplementaria, exceso en dia de semana)
            # supplementary_hours = 100% (Extraordinaria, fin de semana)
            rec.overtime_hours = total_supp_50  # 50%
            rec.supplementary_hours = total_extra_100  # 100%

    def _compute_income_tax_2026(self, monthly_income, monthly_iess):
        """
        Implementation of Resolution NAC-DGERCGC25-00000043.
        1. Project Annual Income (Income * 12).
        2. Deduct IESS Personal (Income * 0.0945 * 12).
        3. Determine Tax Base.
        4. Calculate Impuesto Causado (Progressive Table).
        5. Calculate Rebaja Tributaria (Family Loads).
        6. Result: Annual Tax / 12.
        """
        # A. Projection
        # Note: Decimals and Reserve Funds are EXEMPT from Income Tax.
        annual_gross = monthly_income * 12.0
        annual_deductible_iess = monthly_iess * 12.0

        taxable_base = max(0.0, annual_gross - annual_deductible_iess)

        # B. Impuesto Causado
        # Get tax from l10n_ec.tax.table
        tax_table = self.env["l10n_ec.tax.table"]
        annual_caused_tax = tax_table.get_tax_for_base(taxable_base, year=2026)

        # If no tax caused, return 0 early
        if annual_caused_tax <= 0:
            return 0.0

        # C. Rebaja Tributaria (Tax Credit)
        # Needs Employee Family Loads and Contract Projected Expenses
        basket_model = self.env["l10n_ec.family.basket"]

        # Get Projected Expenses from Contract
        projected_expenses = 0.0
        if self.contract_id:
            projected_expenses = self.contract_id.l10n_ec_projected_expenses

        # Get Family Loads from Employee
        loads = 0
        catastrophic_disease = False
        if self.employee_id:
            loads = self.employee_id.l10n_ec_family_loads
            catastrophic_disease = self.employee_id.l10n_ec_catastrophic_disease

        rebate = basket_model.calculate_rebate(
            projected_expenses, loads, catastrophic_disease, year=2026
        )

        # D. Final Tax
        final_annual_tax = max(0.0, annual_caused_tax - rebate)

        return final_annual_tax / 12.0

    @api.depends("total_income")
    def _compute_iess(self):
        """
        Calculate IESS contributions using configurable rates.
        Rates from ir.config_parameter - NO HARDCODED FALLBACKS.
        """
        ICP = self.env["ir.config_parameter"].sudo()

        # Get IESS rates from config - NO HARDCODED DEFAULTS
        iess_personal_param = ICP.get_param("l10n_ec.iess_aporte_personal")
        iess_employer_param = ICP.get_param("l10n_ec.iess_aporte_patronal")

        if not iess_personal_param or not iess_employer_param:
            raise ValueError(
                "Missing IESS configuration. "
                "Please configure l10n_ec.iess_aporte_personal and l10n_ec.iess_aporte_patronal "
                "in System Parameters or install l10n_ec_hr_payroll properly."
            )

        iess_personal_rate = float(iess_personal_param) / 100
        iess_employer_rate = float(iess_employer_param) / 100

        for rec in self:
            # IESS Personal contribution
            rec.iess_personal = rec.total_income * iess_personal_rate
            # IESS Employer contribution
            rec.iess_employer = rec.total_income * iess_employer_rate

    @api.depends(
        "total_income",
        "contract_id.l10n_ec_accumulate_13",
        "contract_id.l10n_ec_accumulate_14",
        "contract_id.l10n_ec_accumulate_reserve",
    )
    def _compute_benefits(self):
        # Fetch SBU from Config Parameter - NO HARDCODED FALLBACK
        sbu_param = self.env["ir.config_parameter"].sudo().get_param("l10n_ec.sbu")
        if not sbu_param:
            raise ValueError(
                "Missing SBU configuration. "
                "Please configure l10n_ec.sbu in System Parameters or install l10n_ec properly."
            )
        sbu = float(sbu_param)

        for rec in self:
            # 13th: Total Income / 12
            rec.thirteenth = rec.total_income / 12.0

            # 14th: SBU / 12 (if worked full month)
            # Logic: SBU / 360 * days_worked (standard 30-day month)
            rec.fourteenth = (sbu / 360.0) * rec.days_worked

            # Reserve Funds: 8.3333...% of Total Income (usually after 1 year)
            # 1 / 12 = 0.083333...
            rec.reserve_funds = rec.total_income * (1.0 / 12.0)

            # Determine Cash Payout (Mensualizado) vs Accumulation (Provision only)
            cash_total = 0.0
            contract = rec.contract_id

            # If NOT accumulating, pay it now
            if contract and not contract.l10n_ec_accumulate_13:
                cash_total += rec.thirteenth

            if contract and not contract.l10n_ec_accumulate_14:
                cash_total += rec.fourteenth

            if contract and not contract.l10n_ec_accumulate_reserve:
                cash_total += rec.reserve_funds

            rec.total_benefits_cash = cash_total

    @api.constrains("overtime_hours", "supplementary_hours")
    def _check_overtime_limits(self):
        """
        Enforce Código de Trabajo Art. 55:
        - Max 4 hours per day (Cannot check without daily logs).
        - Max 12 hours per week.

        Since this is a monthly/period payslip, we check the weekly limit * 4 weeks.
        Limit: 12 * 4 = 48 hours per month (approx).

        Strict compliance would require daily timesheets, but we enforce the monthly cap here.
        """
        for rec in self:
            total_ot = rec.overtime_hours + rec.supplementary_hours
            # Rough approximation: 4 weeks per month.
            # 12 hours * 4 weeks = 48 hours max per month.
            # This is a safe upper bound to prevent illegal exploitation.
            if total_ot > 48.0:
                from odoo.exceptions import ValidationError

                raise ValidationError(
                    "Legal Overtime Limit Exceeded (Art. 55 Código de Trabajo).\n\n"
                    "The maximum overtime allowed is 12 hours per week.\n"
                    "Accumulated Monthly Limit (approx): 48 hours.\n"
                    f"Current Total: {total_ot} hours.\n\n"
                    "Please reduce the overtime hours."
                )

    def action_confirm(self):
        self._check_overtime_limits()
        self.write({"state": "done"})

    @api.model
    def create(self, vals):
        res = super(L10nEcPayslip, self).create(vals)
        res.name = f"{res.employee_id.name} - {res.date_start}"
        return res
