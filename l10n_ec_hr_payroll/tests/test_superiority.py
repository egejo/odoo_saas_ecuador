from odoo.tests.common import TransactionCase
from datetime import datetime


class TestSuperiorityFeatures(TransactionCase):

    def setUp(self):
        super(TestSuperiorityFeatures, self).setUp()
        self.employee = self.env["hr.employee"].create({"name": "Test Worker"})
        self.contract = self.env["hr.contract"].create(
            {
                "name": "Test Contract",
                "employee_id": self.employee.id,
                "wage": 500.0,
                "state": "open",
            }
        )
        self.payslip_model = self.env["l10n_ec.payslip"]
        self.attendance_model = self.env["hr.attendance"]

    def test_auto_overtime_calculation(self):
        """
        Verify that:
        1. Weekday > 8 hours generates 50% Overtime.
        2. Weekend hours generate 100% Overtime.
        """
        # Create Attendance Records

        # 1. Weekday (Mon): 10 hours work (8 normal + 2 overtime)
        # 2026-01-05 is a Monday
        d1_in = datetime(2026, 1, 5, 8, 0, 0)
        d1_out = datetime(2026, 1, 5, 18, 0, 0)  # 10 hours
        self.attendance_model.create(
            {"employee_id": self.employee.id, "check_in": d1_in, "check_out": d1_out}
        )

        # 2. Weekend (Sat): 4 hours work
        # 2026-01-10 is a Saturday
        d2_in = datetime(2026, 1, 10, 9, 0, 0)
        d2_out = datetime(2026, 1, 10, 13, 0, 0)  # 4 hours
        self.attendance_model.create(
            {"employee_id": self.employee.id, "check_in": d2_in, "check_out": d2_out}
        )

        # Create Payslip
        payslip = self.payslip_model.create(
            {
                "employee_id": self.employee.id,
                "contract_id": self.contract.id,
                "date_start": "2026-01-01",
                "date_end": "2026-01-31",
            }
        )

        # Trigger Computation (which calls _compute_totals -> _compute_overtime_from_attendance)
        payslip._compute_totals()

        # Assertions
        # Weekday: 10h total -> 2h excess -> 50% Overtime
        # Note: In our model, 'overtime_hours' field label is "Overtime (50%) Hours"
        self.assertAlmostEqual(
            payslip.overtime_hours,
            2.0,
            msg="Should have 2.0 hours of 50% OT from weekday",
        )

        # Weekend: 4h total -> All 4h are 100%
        # Note: In our model, 'supplementary_hours' field label is "Supplementary (100%) Hours"
        self.assertAlmostEqual(
            payslip.supplementary_hours,
            4.0,
            msg="Should have 4.0 hours of 100% OT from weekend",
        )

        print("Test Passed: Auto-Overtime logic is correct.")
