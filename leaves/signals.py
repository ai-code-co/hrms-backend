from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Leave, LeaveBalance


@receiver(post_save, sender=Leave)
def update_balance_on_leave_create(sender, instance, created, **kwargs):
    """
    Automatically update leave balance when a new leave is created.
    Deducts from 'pending' balance immediately (optimistic approach).
    """
    if created:
        try:
            balance = LeaveBalance.objects.get(
                employee=instance.employee,
                leave_type=instance.leave_type,
                year=instance.from_date.year
            )
            
            # Deduct from pending balance immediately
            balance.pending += instance.no_of_days
            balance.save()
            
        except LeaveBalance.DoesNotExist:
            # Balance should exist (validated in serializer), but handle gracefully
            pass


@receiver(pre_save, sender=Leave)
def update_balance_on_status_change(sender, instance, **kwargs):
    """
    Automatically update leave balance when leave status changes.
    Handles: Pending → Approved, Pending → Rejected, Approved → Cancelled
    """
    if not instance.pk:
        # New leave, handled by post_save
        return
    
    try:
        # Get the old leave object to compare status
        old_leave = Leave.objects.get(pk=instance.pk)
        old_status = old_leave.status
        new_status = instance.status
        
        # Only update if status actually changed
        if old_status == new_status:
            return
        
        # Get the balance
        balance = LeaveBalance.objects.get(
            employee=instance.employee,
            leave_type=instance.leave_type,
            year=instance.from_date.year
        )
        
        # Handle status transitions
        if old_status == 'Pending' and new_status == 'Approved':
            # Move from pending to used
            balance.pending -= instance.no_of_days
            balance.used += instance.no_of_days
        
        elif old_status == 'Pending' and new_status == 'Rejected':
            # Restore balance (remove from pending)
            balance.pending -= instance.no_of_days
        
        elif old_status == 'Approved' and new_status == 'Cancelled':
            # Restore balance (remove from used)
            balance.used -= instance.no_of_days
        
        elif old_status == 'Pending' and new_status == 'Cancelled':
            # Restore balance (remove from pending)
            balance.pending -= instance.no_of_days
        
        balance.save()
        
    except Leave.DoesNotExist:
        # Shouldn't happen, but handle gracefully
        pass
    except LeaveBalance.DoesNotExist:
        # Balance doesn't exist, can't update
        pass
