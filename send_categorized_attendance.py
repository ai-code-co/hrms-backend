import os
import django
from datetime import date, datetime
import calendar
from django.utils import timezone

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.models import Employee
from attendance.models import Attendance
from notifications.slack_utils import SlackNotificationService

def send_categorized_report():
    today = date(2025, 12, 23) # Hardcoding date for matching prototype
    day_name = today.strftime("%A")
    date_str = today.strftime("%Y-%m-%d")
    
    # 1. On Leave
    on_leave_employees = Employee.objects.filter(
        leaves__from_date__lte=today,
        leaves__to_date__gte=today,
        leaves__status='Approved'
    ).distinct()
    on_leave_names = [e.get_full_name() for e in on_leave_employees]
    
    # 2. On Time
    # In a real scenario we compare with office_working_hours
    # For prototype demo, we'll manually categorize based on logic or mocked data
    
    all_employees = Employee.objects.all()
    on_time_names = []
    late_comer_names = []
    has_not_come_names = []
    
    for emp in all_employees:
        if emp.get_full_name() in on_leave_names:
            continue
            
        attendance = Attendance.objects.filter(employee=emp, date=today).first()
        if not attendance or not attendance.office_in_time:
            has_not_come_names.append(emp.get_full_name())
        else:
            # logic for late
            wh_hour, wh_min = 9, 30 # Default
            if attendance.office_working_hours and ":" in attendance.office_working_hours:
                wh_hour, wh_min = map(int, attendance.office_working_hours.split(":"))
            
            is_late = attendance.office_in_time.time() > timezone.datetime.strptime(f"{wh_hour}:{wh_min}", "%H:%M").time()
            if is_late:
                late_comer_names.append(emp.get_full_name())
            else:
                on_time_names.append(emp.get_full_name())

    # Send reports
    SlackNotificationService.send_attendance_report(date_str, day_name, "On Leave", on_leave_names)
    SlackNotificationService.send_attendance_report(date_str, day_name, "On Time", on_time_names)
    SlackNotificationService.send_attendance_report(date_str, day_name, "Late Comers", late_comer_names)
    SlackNotificationService.send_attendance_report(date_str, day_name, "Has not come yet", has_not_come_names)
    
    print("Attendance reports sent successfully.")

if __name__ == "__main__":
    send_categorized_report()
