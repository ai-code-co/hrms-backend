from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
# MIGRATION: Changed from User to Employee model (2025-12-22)
# from employees.models import Employee

class Leave(models.Model):
    class LeaveType(models.TextChoices):
        CASUAL_LEAVE = 'Casual Leave', _('Casual Leave')
        SICK_LEAVE = 'Sick Leave', _('Sick Leave')
        EARNED_LEAVE = 'Earned Leave', _('Earned Leave')
        UNPAID_LEAVE = 'Unpaid Leave', _('Unpaid Leave')
        MATERNITY_LEAVE = 'Maternity Leave', _('Maternity Leave')
        PATERNITY_LEAVE = 'Paternity Leave', _('Paternity Leave')
        OTHER = 'Other', _('Other')

    class Status(models.TextChoices):
        PENDING = 'Pending', _('Pending')
        APPROVED = 'Approved', _('Approved')
        REJECTED = 'Rejected', _('Rejected')
        CANCELLED = 'Cancelled', _('Cancelled')

    # OLD CODE (Before 2025-12-22): Connected to User model
    # employee = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     related_name='leaves'
    # )
    
    # NEW CODE (2025-12-22): Changed to Employee model
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leaves',
        help_text="Employee applying for leave"
    )
    leave_type = models.CharField(
        max_length=50,
        choices=LeaveType.choices,
        default=LeaveType.CASUAL_LEAVE
    )
    from_date = models.DateField()
    to_date = models.DateField()
    no_of_days = models.DecimalField(max_digits=5, decimal_places=1, default=1.0)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    day_status = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. First Half, Second Half")
    late_reason = models.TextField(blank=True, null=True)
    doc_link = models.CharField(max_length=500, blank=True, null=True, help_text="Path to document (e.g. hrms/uploads/abc123.jpg)")
    rejection_reason = models.TextField(blank=True, null=True)
    rh_dates = models.JSONField(default=list, blank=True, help_text="List of Restricted Holiday dates")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.from_date} to {self.to_date})"


class LeaveQuota(models.Model):
    """
    Defines leave quotas for employees.
    Admin configures how many leaves each employee gets per month/year.
    """
    # OLD CODE: employee = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    # NEW CODE (2025-12-22): Changed to Employee model
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_quotas',
        help_text="Employee for whom quota is configured"
    )
    leave_type = models.CharField(
        max_length=50,
        choices=Leave.LeaveType.choices
    )
    monthly_quota = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Leaves allocated per month"
    )
    yearly_quota = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Total leaves allocated per year"
    )
    rh_quota = models.IntegerField(
        default=2,
        help_text="Number of Restricted Holidays allowed per year"
    )
    carry_forward_limit = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Maximum leaves that can be carried forward to next year"
    )
    effective_from = models.DateField(help_text="Quota effective from this date")
    effective_to = models.DateField(null=True, blank=True, help_text="Quota valid until this date")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_from']
        unique_together = ['employee', 'leave_type', 'effective_from']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.yearly_quota} days/year)"


class LeaveBalance(models.Model):
    """
    Tracks current leave balance for each employee.
    Auto-calculated based on quotas, approved leaves, and carry forwards.
    """
    # OLD CODE: employee = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    # NEW CODE (2025-12-22): Changed to Employee model
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_balances',
        help_text="Employee whose balance is tracked"
    )
    leave_type = models.CharField(
        max_length=50,
        choices=Leave.LeaveType.choices
    )
    year = models.IntegerField(help_text="Fiscal year (e.g., 2025)")
    
    # Allocations
    total_allocated = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Total allocated (quota + carry forward)"
    )
    carried_forward = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Leaves carried forward from previous year"
    )
    
    # Usage
    used = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Approved leaves taken"
    )
    pending = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Leaves pending approval"
    )
    
    # RH Tracking
    rh_allocated = models.IntegerField(default=0, help_text="RH days allocated")
    rh_used = models.IntegerField(default=0, help_text="RH days used")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', 'employee']
        unique_together = ['employee', 'leave_type', 'year']

    @property
    def available(self):
        """Calculate available leaves"""
        return self.total_allocated - self.used - self.pending
    
    @property
    def rh_available(self):
        """Calculate available RH days"""
        return self.rh_allocated - self.rh_used

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year}): {self.available}/{self.total_allocated}"


class RestrictedHoliday(models.Model):
    """
    Restricted Holidays (RH) that employees can choose to take.
    """
    date = models.DateField(unique=True)
    name = models.CharField(max_length=200, help_text="Name of the restricted holiday")
    description = models.TextField(blank=True, help_text="Additional details")
    is_active = models.BooleanField(default=True, help_text="Whether this RH is currently available")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"

