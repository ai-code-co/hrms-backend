import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.models import Employee
from leaves.models import Leave

def trigger_test_leaves():
    print("--- Triggering Test Leave Requests ---")
    
    # Excellence Tech
    try:
        emp_et = Employee.objects.get(email="hr@excellencetech.com")
        print(f"Creating leave for {emp_et.get_full_name()} (Excellence Tech)...")
        Leave.objects.create(
            employee=emp_et,
            leave_type=Leave.LeaveType.CASUAL_LEAVE,
            from_date=date.today() + timedelta(days=1),
            to_date=date.today() + timedelta(days=2),
            no_of_days=2,
            reason="Testing Excellence Tech Slack Notification",
            status=Leave.Status.PENDING
        )
    except Employee.DoesNotExist:
        print("❌ Error: Excellence Tech test employee not found.")

    # SuccesPoint
    try:
        emp_sp = Employee.objects.get(email="hr@succespoint.com")
        print(f"Creating leave for {emp_sp.get_full_name()} (SuccesPoint)...")
        Leave.objects.create(
            employee=emp_sp,
            leave_type=Leave.LeaveType.CASUAL_LEAVE,
            from_date=date.today() + timedelta(days=1),
            to_date=date.today() + timedelta(days=2),
            no_of_days=2,
            reason="Testing SuccesPoint Slack Notification",
            status=Leave.Status.PENDING
        )
    except Employee.DoesNotExist:
        print("❌ Error: SuccesPoint test employee not found.")

    print("\n✅ Leave requests created. Check your Slack management channels!")

if __name__ == "__main__":
    trigger_test_leaves()
