from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from leaves.models import Leave
from .models import Attendance

@receiver(post_save, sender=Leave)
def sync_leave_to_attendance(sender, instance, created, **kwargs):
    """
    Synchronize Leave status with Attendance records.
    When a leave is approved, create/update corresponding attendance records.
    """
    from .services import AttendanceCalculationService

    if instance.status in ['Approved', 'APPROVED']:
        # Iterate through the date range of the leave
        current_date = instance.from_date
        while current_date <= instance.to_date:
            # Skip weekends (Sat=5, Sun=6)
            # determine_day_type handles this better, but we only create if it's a working day
            # Actually, let's create/update and then let determine_day_type fix it
            
            att, created = Attendance.objects.get_or_create(
                employee=instance.employee,
                date=current_date
            )
            att.leave = instance
            AttendanceCalculationService.determine_day_type(att)
            att.save()
            
            current_date += timedelta(days=1)
    else:
        # If leave is not approved (e.g., cancelled or rejected), 
        # find affected attendances and revert them
        affected_attendances = Attendance.objects.filter(leave=instance)
        for att in affected_attendances:
            att.leave = None
            AttendanceCalculationService.determine_day_type(att)
            att.save()

@receiver(post_delete, sender=Leave)
def cleanup_attendance_on_leave_delete(sender, instance, **kwargs):
    """Clear leave link if leave is deleted"""
    Attendance.objects.filter(leave=instance).update(leave=None)
