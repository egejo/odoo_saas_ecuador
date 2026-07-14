# -*- coding: utf-8 -*-
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class L10nEcVacationLedger(models.Model):
    _name = "l10n_ec.vacation.ledger"
    _description = "Ecuadorian Vacation Ledger"
    _order = "date desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    contract_id = fields.Many2one("hr.contract", string="Contract", required=True)

    date = fields.Date("Date", default=fields.Date.today, required=True)
    description = fields.Char("Description", required=True)

    # Marca las lineas generadas por run_monthly_accrual, para poder
    # detectar si ya se corrio el devengo de un mes/contrato en particular
    # y no duplicarlo -- antes no habia ninguna proteccion (reconocido en
    # el propio codigo original como "Omitted for MVP simplicity").
    is_monthly_accrual = fields.Boolean(default=False)

    # Ledger columns
    days_earned = fields.Float(
        "Days Earned (+)", default=0.0, help="Accrual (1.25/month + seniority)"
    )
    days_taken = fields.Float(
        "Days Taken (-)", default=0.0, help="Vacation days enjoyed"
    )
    days_paid = fields.Float(
        "Days Paid (-)", default=0.0, help="Liquidated days (cash)"
    )

    balance = fields.Float("Balance", compute="_compute_balance", store=True)

    @api.depends("employee_id", "date", "days_earned", "days_taken", "days_paid")
    def _compute_balance(self):
        # Saldo corriente real (acumulado cronologicamente hasta esta linea
        # inclusive), no un gran total repetido en cada fila -- ver el bug
        # real corregido 2026-07-14: el compute original hacia
        # search([employee_id=...]) sin filtrar por fecha, asi que TODA
        # linea de un empleado mostraba el mismo total actual, y ademas
        # ese total quedaba congelado en cada linea vieja (Odoo solo
        # recalcula un compute cuando cambian los campos de los que
        # depende ESE mismo registro, no cuando se crea/edita un
        # hermano) -- create/write/unlink abajo fuerzan el recalculo de
        # todos los hermanos del mismo empleado cuando corresponde.
        for rec in self:
            if not rec.employee_id:
                rec.balance = 0.0
                continue
            siblings = self.search(
                [("employee_id", "=", rec.employee_id.id)], order="date asc, id asc"
            )
            running = 0.0
            for line in siblings:
                running += line.days_earned - line.days_taken - line.days_paid
                if line.id == rec.id:
                    break
            rec.balance = running

    def _recompute_siblings_balance(self, employees):
        """Fuerza el recalculo del saldo corriente de TODAS las lineas de
        estos empleados -- necesario porque insertar/editar/borrar una
        linea cambia el saldo corriente de las lineas posteriores (o de
        todas, si la nueva linea no es la mas reciente), y el compute por
        si solo no se re-dispara para hermanos."""
        if not employees:
            return
        siblings = self.search([("employee_id", "in", employees.ids)])
        siblings.invalidate_recordset(["balance"])
        siblings._compute_balance()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._recompute_siblings_balance(records.employee_id)
        return records

    def write(self, vals):
        employees_before = self.employee_id
        res = super().write(vals)
        employees_after = self.employee_id
        if any(
            f in vals
            for f in ("days_earned", "days_taken", "days_paid", "date", "employee_id")
        ):
            self._recompute_siblings_balance(employees_before | employees_after)
        return res

    def unlink(self):
        employees = self.employee_id
        res = super().unlink()
        self._recompute_siblings_balance(employees)
        return res

    @api.model
    def run_monthly_accrual(self, reference_date=None):
        """
        Scheduled Action to run accruals.
        Logic:
        1. Find active contracts.
        2. Calculate seniority (Years of service).
        3. Base = 1.25.
        4. Art. 69: +1 dia por cada año excedente desde el 6to año, tope
           15 dias adicionales (maximo 30 dias totales/año) -- confirmado
           contra el texto real del Art. 69 via busqueda web 2026-07-14,
           el cap de 15 SI es real (no era una duda sin resolver como
           decia el comentario original).
        """
        if not reference_date:
            reference_date = fields.Date.today()

        period_start = reference_date.replace(day=1)
        period_end = period_start + relativedelta(months=1, days=-1)

        contracts = self.env["hr.contract"].search([("state", "=", "open")])

        for contract in contracts:
            # Evitar duplicar el devengo si este metodo ya corrio para este
            # contrato en este mismo mes (cron duplicado, corrida manual
            # repetida, etc.) -- antes no habia ninguna proteccion y
            # correrlo dos veces duplicaba el devengo silenciosamente.
            already_ran = self.search_count(
                [
                    ("contract_id", "=", contract.id),
                    ("is_monthly_accrual", "=", True),
                    ("date", ">=", period_start),
                    ("date", "<=", period_end),
                ]
            )
            if already_ran:
                continue

            # 1. Base Accrual
            accrual = 1.25

            # 2. Seniority Bonus
            # Calculate seniority
            start_date = contract.date_start
            # Service years
            delta = relativedelta(reference_date, start_date)
            years_service = delta.years

            seniority_days_yearly = 0.0
            if years_service > 5:
                extra_years = years_service - 5
                seniority_days_yearly = min(
                    extra_years, 15
                )  # Cap additional days at 15 (confirmado, real)

            seniority_monthly = seniority_days_yearly / 12.0
            total_earned = accrual + seniority_monthly

            self.create(
                {
                    "employee_id": contract.employee_id.id,
                    "contract_id": contract.id,
                    "date": reference_date,
                    "description": f"Monthly Accrual ({reference_date.strftime('%B %Y')}) - Base: 1.25, Seniority: {seniority_monthly:.2f}",
                    "days_earned": total_earned,
                    "is_monthly_accrual": True,
                }
            )
