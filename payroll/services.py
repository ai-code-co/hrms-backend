from datetime import date, timedelta, datetime
import calendar
from django.db.models import Sum, Q
from decimal import Decimal
from leaves.models import Leave, LeaveBalance, LeaveQuota
from holidays.models import Holiday
from attendance.models import Attendance
from attendance.services import AttendanceCalculationService
from .models import SalaryStructure, Payslip

class PayrollService:
    @staticmethod
    def calculate_monthly_salary(employee, month, year):
        """
        Calculates the salary for an employee for a specific month.
        Automated based on Attendance and Approved Leaves.
        """
        # 1. Get Salary Structure
        salary_structure = SalaryStructure.objects.filter(employee=employee, is_active=True).first()
        if not salary_structure:
            return None

        # 2. Get Month Range
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # 3. Calculate Attendance/Working Days automatically
        working_days_count = 0
        absent_days_count = 0
        total_days = last_day
        
        # Fetch all attendance records for this month once to avoid repeated DB hits
        attendance_records = {a.date: a for a in Attendance.objects.filter(
            employee=employee, date__range=[start_date, end_date]
        )}
        
        # Fetch leaves and holidays
        holidays = set(Holiday.objects.filter(
            date__range=[start_date, end_date], is_active=True
        ).values_list('date', flat=True))
        
        # Approved leaves
        approved_leaves = Leave.objects.filter(
            employee=employee,
            status='Approved',
            from_date__lte=end_date,
            to_date__gte=start_date
        )
        
        leave_dates = {}
        for l in approved_leaves:
            curr = max(l.from_date, start_date)
            limit = min(l.to_date, end_date)
            while curr <= limit:
                leave_dates[curr] = l
                curr += timedelta(days=1)

        # 4. Iterate through each day to determine payment status
        for day in range(1, last_day + 1):
            curr_date = date(year, month, day)
            
            # Skip if before joining
            if employee.joining_date and curr_date < employee.joining_date:
                continue
                
            # If it's a weekend or holiday, it's a paid non-working day
            if curr_date.weekday() >= 5 or curr_date in holidays:
                continue

            # Check attendance
            att = attendance_records.get(curr_date)
            leave = leave_dates.get(curr_date)
            
            if att and ((att.office_in_time and att.office_out_time) or 
                       (att.home_in_time and att.home_out_time) or
                       (att.in_time and att.out_time)):
                working_days_count += 1
            elif leave:
                # If on paid leave, it counts as working/paid
                if leave.leave_type != Leave.LeaveType.UNPAID_LEAVE:
                    working_days_count += 1
                else:
                    absent_days_count += 1
            else:
                # No attendance and no leave = Absent (Undeducted)
                absent_days_count += 1

        # 5. Financial Calculations
        gross_salary = salary_structure.total_earnings
        daily_rate = gross_salary / Decimal(total_days)
        
        unpaid_leave_deduction = absent_days_count * daily_rate
        statutory_deductions = salary_structure.epf + salary_structure.tds
        net_salary = gross_salary - statutory_deductions - unpaid_leave_deduction

        # 6. Fetch Leave Balance Info
        total_allocated = Decimal('0')
        remaining_balance = Decimal('0')
        balance_obj = LeaveBalance.objects.filter(employee=employee, year=year).first()
        if balance_obj:
            total_allocated = balance_obj.total_allocated
            remaining_balance = balance_obj.remaining

        return {
            "month": month,
            "year": year,
            "gross_salary": gross_salary,
            "working_days": working_days_count,
            "absent_days": absent_days_count,
            "statutory_deductions": statutory_deductions,
            "unpaid_leave_deduction": unpaid_leave_deduction.quantize(Decimal('0.01')),
            "net_salary": net_salary.quantize(Decimal('0.01')),
            "leave_balance": remaining_balance,
            "allocated_leaves": total_allocated,
            "daily_rate": daily_rate.quantize(Decimal('0.01'))
        }
