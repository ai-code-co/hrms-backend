from django.db.models.signals import post_save
from django.dispatch import receiver
from leaves.models import Leave
from payroll.models import Payslip
from attendance.models import Attendance
from employees.models import Employee

from .slack_utils import SlackNotificationService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Leave)
def handle_leave_notification(sender, instance, created, **kwargs):
    try:
        if created:
            # 1. Notify the Employee (DM)
            SlackNotificationService.notify_leave_applied(instance.employee, instance)
            
            # 2. Notify Management Channel with Buttons
            SlackNotificationService.notify_management_leave_request(instance)
        else:
            # Check if status was updated
            if 'status' in (kwargs.get('update_fields') or []):
                if instance.status in ['Approved', 'Rejected']:
                    SlackNotificationService.notify_leave_status(instance.employee, instance, instance.status)
    except Exception as e:
        logger.error(f"Error in leave notification signal: {e}")

@receiver(post_save, sender=Payslip)
def handle_payslip_notification(sender, instance, created, **kwargs):
    try:
        if created or instance.status == 'published':
            import calendar
            month_name = calendar.month_name[instance.month]
            SlackNotificationService.notify_payslip_generated(instance.employee, month_name)
    except Exception as e:
        logger.error(f"Error in payslip notification signal: {e}")

@receiver(post_save, sender=Attendance)
def handle_attendance_notification(sender, instance, created, **kwargs):
    try:
        from django.utils import timezone
        import calendar

        # 1. Daily Punch-in Notification
        if created and instance.office_in_time:
            # Find previous working day session
            prev_attendance = Attendance.objects.filter(
                employee=instance.employee,
                date__lt=instance.date,
                day_type='WORKING_DAY'
            ).order_by('-date').first()
            
            prev_entry = "N/A"
            prev_exit = "N/A"
            if prev_attendance:
                prev_entry = prev_attendance.office_in_time.strftime("%I:%M %p") if prev_attendance.office_in_time else "N/A"
                prev_exit = prev_attendance.office_out_time.strftime("%I:%M %p") if prev_attendance.office_out_time else "N/A"
            
            today_entry = instance.office_in_time.strftime("%I:%M %p")
            
            # Check for Late Alerts (more than 4 times this month)
            # Define "late" as after office_working_hours + 30 mins (example: 09:30 + 30m = 10:00 AM)
            # Or just after office_working_hours? Prototype shows late on 11:05 AM.
            
            # Extract hour/minute from office_working_hours (e.g. "09:00")
            wh_hour, wh_min = 9, 0
            if instance.office_working_hours and ":" in instance.office_working_hours:
                wh_hour, wh_min = map(int, instance.office_working_hours.split(":"))
            
            is_late_today = instance.office_in_time.time() > timezone.datetime.strptime(f"{wh_hour}:{wh_min}", "%H:%M").time()
            
            if is_late_today:
                month_start = instance.date.replace(day=1)
                month_end = instance.date.replace(day=calendar.monthrange(instance.date.year, instance.date.month)[1])
                
                # Find all late days this month
                # For simplicity, we compare time() with the work hours
                # In a real app we might use a field, but here we query
                late_records = Attendance.objects.filter(
                    employee=instance.employee,
                    date__gte=month_start,
                    date__lte=instance.date,
                    office_in_time__isnull=False
                )
                
                late_days = []
                for rec in late_records:
                    if rec.office_in_time.time() > timezone.datetime.strptime(f"{wh_hour}:{wh_min}", "%H:%M").time():
                        late_days.append(rec.date.strftime("%dth"))
                
                if len(late_days) > 4:
                    late_dates_str = ", ".join(late_days)
                    SlackNotificationService.notify_late_alert(
                        instance.employee,
                        late_dates_str,
                        today_entry,
                        prev_entry,
                        prev_exit
                    )
                    return # Skip normal daily notification if late alert sent

            # Normal Daily Notification
            SlackNotificationService.notify_daily_attendance(
                instance.employee,
                prev_entry,
                prev_exit,
                today_entry
            )
        
        elif created and not instance.office_in_time:
            # New record created but no entry time yet
            SlackNotificationService.notify_missing_attendance(instance.employee, instance.date.strftime("%Y-%m-%d"))

        # 2. Timing Update Notification (triggered when reason 'text' is provided)
        elif not created:
            if instance.text:
                SlackNotificationService.notify_attendance_update(
                    instance.employee,
                    instance.date.strftime("%d-%m-%Y"),
                    instance.office_in_time.strftime("%I:%M %p") if instance.office_in_time else "N/A",
                    instance.office_out_time.strftime("%I:%M %p") if instance.office_out_time else "N/A",
                    instance.text or "N/A"
                )
    except Exception as e:
        logger.error(f"Error in attendance notification signal: {e}")

from attendance.models import Timesheet, ManualAttendanceRequest

@receiver(post_save, sender=Timesheet)
def handle_timesheet_notification(sender, instance, created, **kwargs):
    try:
        if created:
            # 1. Notify Management
            SlackNotificationService.notify_management_timesheet_request(instance)
            # 2. Notify Employee
            SlackNotificationService.notify_timesheet_submitted(
                instance.employee, 
                instance.start_date.strftime("%A, %d-%b-%Y"), 
                instance.end_date.strftime("%A, %d-%b-%Y")
            )
        elif not created:
            update_fields = kwargs.get('update_fields') or []
            if 'status' in update_fields and instance.status in ['approved', 'rejected']:
                SlackNotificationService.notify_attendance_approval(
                    instance.employee, 
                    instance.start_date.strftime("%A, %d-%b-%Y"), 
                    instance.status.capitalize()
                )
    except Exception as e:
        logger.error(f"Error in timesheet notification signal: {e}")

@receiver(post_save, sender=ManualAttendanceRequest)
def handle_manual_attendance_notification(sender, instance, created, **kwargs):
    try:
        if created:
            SlackNotificationService.notify_manual_attendance_request(instance)
        elif not created:
            update_fields = kwargs.get('update_fields') or []
            if 'status' in update_fields and instance.status == 'approved':
                SlackNotificationService.notify_manual_attendance_approved(
                    instance.employee,
                    instance.date.strftime("%d-%m-%Y"),
                    instance.entry_time.strftime("%I:%M %p"),
                    instance.exit_time.strftime("%I:%M %p")
                )
    except Exception as e:
        logger.error(f"Error in manual attendance notification signal: {e}")

@receiver(post_save, sender=Employee)
def handle_employee_welcome_notification(sender, instance, created, **kwargs):
    try:
        if created:
            SlackNotificationService.notify_welcome(instance)
    except Exception as e:
        logger.error(f"Error in employee welcome notification signal: {e}")
