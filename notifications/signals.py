from django.db.models.signals import post_save
from django.dispatch import receiver
from leaves.models import Leave
from payroll.models import Payslip

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

# @receiver(post_save, sender=Attendance)
# def handle_attendance_notification(sender, instance, created, **kwargs):
#     try:
#         if created:
#             # For new entry
#             # In a real system we'd compare with previous day's entry/exit
#             # For now just send today's entry
#             SlackNotificationService.notify_missing_attendance(instance.employee)
#         elif instance.status == 'approved' and instance.requested_entry_time:
#              SlackNotificationService.notify_attendance_update(
#                  instance.employee, 
#                  instance.date, 
#                  instance.entry_time, 
#                  instance.exit_time,
#                  instance.correction_reason
#              )
#     except Exception as e:
#         logger.error(f"Error in attendance notification signal: {e}")

# @receiver(post_save, sender=Timesheet)
# def handle_timesheet_notification(sender, instance, created, **kwargs):
#     try:
#         if created:
#             # Notify Management Channel with Buttons
#             SlackNotificationService.notify_management_timesheet_request(instance)
#         elif not created and instance.status in ['approved', 'rejected']:
#              SlackNotificationService.notify_attendance_approval(
#                  instance.employee, 
#                  instance.date, 
#                  instance.status.capitalize()
#              )
#     except Exception as e:
#         logger.error(f"Error in timesheet notification signal: {e}")
