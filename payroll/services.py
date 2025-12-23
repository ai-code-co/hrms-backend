from datetime import date, timedelta
import calendar
from django.db.models import Sum
from decimal import Decimal
from leaves.models import Leave
from holidays.models import Holiday
from .models import SalaryStructure, Payslip

class PayrollService:
    @staticmethod
    def calculate_monthly_salary(employee, month, year):
        """
        Calculates the salary for an employee for a specific month.
        Includes deductions for unpaid leaves.
        """
        # 1. Get Salary Structure
        salary_structure = SalaryStructure.objects.filter(employee=employee, is_active=True).first()
        if not salary_structure:
            return None

        # 2. Calculate Total Days in Month and Working Days
        _, last_day = calendar.monthrange(year, month)
        total_days = last_day
        
        # 3. Find Unpaid Leaves for the month
        unpaid_leaves = Leave.objects.filter(
            employee=employee,
            leave_type=Leave.LeaveType.UNPAID_LEAVE,
            status=Leave.Status.APPROVED,
            from_date__year=year,
            from_date__month=month
        ).aggregate(total=Sum('no_of_days'))['total'] or Decimal('0')

        # 4. Calculate Daily Rate
        # Normally daily rate = Total Gross / Total Days in Month
        gross_salary = salary_structure.total_earnings
        daily_rate = gross_salary / Decimal(total_days)

        # 5. Calculate Deduction
        unpaid_leave_deduction = unpaid_leaves * daily_rate

        # 6. Calculate Net Salary
        # (Total Earnings - Deductions - Unpaid Leave Deduction)
        statutory_deductions = salary_structure.epf + salary_structure.tds
        net_salary = gross_salary - statutory_deductions - unpaid_leave_deduction

        return {
            "month": month,
            "year": year,
            "gross_salary": gross_salary,
            "statutory_deductions": statutory_deductions,
            "unpaid_leaves": unpaid_leaves,
            "unpaid_leave_deduction": unpaid_leave_deduction.quantize(Decimal('0.01')),
            "daily_rate": daily_rate.quantize(Decimal('0.01')),
            "net_salary": net_salary.quantize(Decimal('0.01')),
            "total_days": total_days
        }
