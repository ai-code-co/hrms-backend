from django.db.models.signals import post_save
from django.dispatch import receiver
from auth_app.models import User
from .models import Employee

@receiver(post_save, sender=User)
def sync_user_to_employee(sender, instance, created, **kwargs):
    """
    Sync common fields from User to Employee when User is updated.
    """
    if not created:  # Only for updates, as creation is handled by AdminCreateUserSerializer
        try:
            employee = instance.employee_profile
            # Check if values are actually different to avoid infinite loops
            updates = {}
            if employee.first_name != instance.first_name:
                updates['first_name'] = instance.first_name
            if employee.last_name != instance.last_name:
                updates['last_name'] = instance.last_name
            if employee.email != instance.email:
                updates['email'] = instance.email
            
            if updates:
                Employee.objects.filter(id=employee.id).update(**updates)
        except Employee.DoesNotExist:
            pass

@receiver(post_save, sender=Employee)
def sync_employee_to_user(sender, instance, created, **kwargs):
    """
    Sync common fields from Employee to User when Employee is updated.
    """
    if instance.user:
        user = instance.user
        updates = {}
        if user.first_name != instance.first_name:
            updates['first_name'] = instance.first_name
        if user.last_name != instance.last_name:
            updates['last_name'] = instance.last_name
        if user.email != instance.email:
            updates['email'] = instance.email
        
        if updates:
            User.objects.filter(id=user.id).update(**updates)
