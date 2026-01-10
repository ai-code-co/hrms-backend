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
    if instance.status in ['Approved', 'APPROVED']:
        # Iterate through the date range of the leave
        current_date = instance.from_date
        while current_date <= instance.to_date:
            # Determine day_type based on whether it's a partial leave
            # Note: We assume day_status contains info about half-days
            is_partial = False
            if hasattr(instance, 'day_status') and instance.day_status:
                if 'Half' in instance.day_status:
                    is_partial = True

            day_type = 'LEAVE_DAY'
            if is_partial:
                day_type = 'WORKING_DAY' # Or maybe a new 'HALF_DAY' type if needed

            # Update or create attendance record
            # Skip weekends (Sat=5, Sun=6)
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            Attendance.objects.update_or_create(
                employee=instance.employee,
                date=current_date,
                defaults={
                    'leave': instance,
                    'day_type': day_type,
                    # We don't overwrite in_time/out_time if it's a partial leave 
                    # as the employee might have worked the other half.
                }
            )
            current_date += timedelta(days=1)
    else:
        # If leave is not approved (e.g., cancelled or rejected), 
        # clear the leave link from related attendance records
        Attendance.objects.filter(leave=instance).update(leave=None)
        # Note: We might want to trigger a recalculation of day_type here 
        # but cleanup is a good first step.

@receiver(post_delete, sender=Leave)
def cleanup_attendance_on_leave_delete(sender, instance, **kwargs):
    """Clear leave link if leave is deleted"""
    Attendance.objects.filter(leave=instance).update(leave=None)
