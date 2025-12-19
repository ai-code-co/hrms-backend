from django.db import models
from django.core.exceptions import ValidationError
from auth_app.models import User
from employees.models import Employee


class DeviceType(models.Model):
    """Device Type/Category model (e.g., LAPTOP, MOBILE PHONE, MOUSE)"""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Device type name (e.g., LAPTOP, MOBILE PHONE)"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the device type"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Device Type'
        verbose_name_plural = 'Device Types'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def total_devices(self):
        """Total count of active devices of this type"""
        return self.devices.filter(is_active=True).count()

    @property
    def working_devices(self):
        """Count of working devices of this type"""
        return self.devices.filter(is_active=True, status='working').count()

    @property
    def unassigned_devices(self):
        """Count of unassigned devices of this type"""
        return self.devices.filter(is_active=True, employee__isnull=True).count()


class Device(models.Model):
    """Individual device model"""
    
    STATUS_CHOICES = [
        ('working', 'Working'),
        ('need_to_sell', 'Need To Sell'),
        ('damaged', 'Damaged'),
        ('repair', 'Under Repair'),
        ('retired', 'Retired'),
        ('lost', 'Lost'),
        ('other', 'Other'),
    ]

    device_type = models.ForeignKey(
        DeviceType,
        on_delete=models.PROTECT,
        related_name='devices',
        help_text="Type/category of the device"
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Device serial number"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='working',
        help_text="Current status of the device"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_devices',
        help_text="Currently assigned employee"
    )
    purchase_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when device was purchased"
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Purchase price of the device"
    )
    warranty_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="Warranty expiry date"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the device"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_devices'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_devices'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        indexes = [
            models.Index(fields=['device_type', 'status']),
            models.Index(fields=['employee']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        device_info = f"{self.device_type.name}"
        if self.serial_number:
            device_info += f" - {self.serial_number}"
        if self.employee:
            device_info += f" (Assigned to {self.employee.get_full_name()})"
        return device_info

    def clean(self):
        """Validate device data"""
        if self.warranty_expiry and self.purchase_date:
            if self.warranty_expiry < self.purchase_date:
                raise ValidationError("Warranty expiry date cannot be before purchase date.")


class DeviceAssignment(models.Model):
    """Device assignment history model"""
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='assignment_history'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='device_assignments'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='device_assignments_made'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    returned_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when device was returned"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about the assignment"
    )

    class Meta:
        ordering = ['-assigned_date']
        verbose_name = 'Device Assignment'
        verbose_name_plural = 'Device Assignments'
        indexes = [
            models.Index(fields=['device', 'employee']),
            models.Index(fields=['assigned_date']),
        ]

    def __str__(self):
        status = "Active" if not self.returned_date else "Returned"
        return f"{self.device.device_type.name} → {self.employee.get_full_name()} ({status})"

