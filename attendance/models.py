from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from employees.models import Employee
from auth_app.models import User
from .services import AttendanceCalculationService
from .constants import ADMIN_ALERT_MESSAGE_MISSING_TIME


class Attendance(models.Model):
    """ Attendance model – FINAL & PRODUCTION SAFE """
    DAY_TYPE_CHOICES = [
        ('WORKING_DAY', 'Working Day'),
        ('HALF_DAY', 'Half Day'),
        ('LEAVE_DAY', 'Leave Day'),
        ('HOLIDAY', 'Holiday'),
        ('WEEKEND_OFF', 'Weekend Off'),
        ('ABSENT', 'Absent'),
        ('FUTURE_DAY', 'Future Day'),
        ('BEFORE_JOINING', 'Before Joining'),
    ]
    
    EXTRA_TIME_STATUS_CHOICES = [
        ('+', 'Overtime'),
        ('-', 'Undertime'),
        ('', 'No Extra Time'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendances',
        
    )

    date = models.DateField(db_index=True)

    # Backward-compatible times
    in_time = models.DateTimeField(null=True, blank=True)
    out_time = models.DateTimeField(null=True, blank=True)

    # Location-based times
    office_in_time = models.DateTimeField(null=True, blank=True)
    office_out_time = models.DateTimeField(null=True, blank=True)
    home_in_time = models.DateTimeField(null=True, blank=True)
    home_out_time = models.DateTimeField(null=True, blank=True)

    office_working_hours = models.CharField(max_length=10, default='09:00')
    orignal_total_time = models.IntegerField(default=32400)

    # Calculated fields
    seconds_actual_worked_time = models.IntegerField(default=0)
    seconds_actual_working_time = models.IntegerField(default=0)
    seconds_extra_time = models.IntegerField(default=0)
    office_time_inside = models.IntegerField(default=0)

    office_seconds_worked = models.IntegerField(default=0)
    home_seconds_worked = models.IntegerField(default=0)

    day_type = models.CharField(
        max_length=20,
        choices=DAY_TYPE_CHOICES,
        default='WORKING_DAY'
    )

    extra_time_status = models.CharField(
        max_length=1,
        choices=EXTRA_TIME_STATUS_CHOICES,
        default='',
        blank=True
    )

    # Alerts
    admin_alert = models.IntegerField(default=0)
    admin_alert_message = models.CharField(max_length=200, blank=True)
    day_text = models.TextField(blank=True)
    text = models.TextField(blank=True)

    # Optional tracking
    standup_time = models.DateTimeField(null=True, blank=True)
    report_time = models.DateTimeField(null=True, blank=True)
    lunch_start_time = models.DateTimeField(null=True, blank=True)
    lunch_end_time = models.DateTimeField(null=True, blank=True)

    # Flags
    is_day_before_joining = models.BooleanField(default=False)
    is_working_from_home = models.BooleanField(default=False)

    # Timesheet Fields
    TIMESHEET_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    timesheet_status = models.CharField(
        max_length=10, 
        choices=TIMESHEET_STATUS_CHOICES, 
        default='APPROVED'
    )
    timesheet_submitted_at = models.DateTimeField(null=True, blank=True)
    timesheet_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_timesheets'
    )
    timesheet_approved_at = models.DateTimeField(null=True, blank=True)
    timesheet_admin_notes = models.TextField(blank=True)
    tracker_screenshot = models.CharField(max_length=500, null=True, blank=True, help_text="Cloudinary public ID / path for the screenshot")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_attendances',
        
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_attendances',
        
    )

    class Meta:
        ordering = ['-date', 'employee']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'date'],
                name='unique_employee_date_attendance'
            )
        ]
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['day_type']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date}"

    def clean(self):
        if self.in_time and self.out_time and self.out_time < self.in_time:
            raise ValidationError("Out time cannot be before in time.")

        for start, end, label in [
            (self.office_in_time, self.office_out_time, "Office"),
            (self.home_in_time, self.home_out_time, "Home"),
        ]:
            if start and end and end < start:
                raise ValidationError(f"{label} out time cannot be before in time.")

            if start and not timezone.is_aware(start):
                raise ValidationError(f"{label} in time must be timezone-aware.")
            if end and not timezone.is_aware(end):
                raise ValidationError(f"{label} out time must be timezone-aware.")

    def save(self, *args, **kwargs):
        self.office_seconds_worked = AttendanceCalculationService.calculate_location_seconds(
            self.office_in_time, self.office_out_time
        )
        self.home_seconds_worked = AttendanceCalculationService.calculate_location_seconds(
            self.home_in_time, self.home_out_time
        )

        total_seconds = AttendanceCalculationService.calculate_total_worked_seconds(self)

        self.in_time = AttendanceCalculationService.get_earliest_checkin(self)
        self.out_time = AttendanceCalculationService.get_latest_checkout(self)

        if total_seconds:
            self.seconds_actual_worked_time = total_seconds
            self.seconds_actual_working_time = total_seconds
            self.office_time_inside = self.office_seconds_worked
            self.seconds_extra_time = AttendanceCalculationService.calculate_extra_seconds(
                total_seconds, self.orignal_total_time
            )
            self.extra_time_status = AttendanceCalculationService.extra_time_status(
                self.seconds_extra_time
            )
        else:
            self.seconds_actual_worked_time = 0
            self.seconds_actual_working_time = 0
            self.office_time_inside = 0
            self.seconds_extra_time = 0
            self.extra_time_status = ''

        if AttendanceCalculationService.should_flag_admin_alert(self):
            self.admin_alert = 1
            self.admin_alert_message = ADMIN_ALERT_MESSAGE_MISSING_TIME
        else:
            self.admin_alert = 0
            self.admin_alert_message = ""

        self.full_clean()
        super().save(*args, **kwargs)


# =========================================================
# DEPENDENT MODELS (REQUIRED BY notifications APP)
# =========================================================

class Timesheet(models.Model):
    """Monthly timesheet submission"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='timesheets',
        
    )
    start_date = models.DateField()
    end_date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.start_date} to {self.end_date}"


class ManualAttendanceRequest(models.Model):
    """Manual correction request for entry/exit times"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='manual_requests',
        
    )
    date = models.DateField()
    entry_time = models.TimeField()
    exit_time = models.TimeField()
    hours = models.CharField(max_length=50, blank=True, null=True)
    reason = models.TextField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} Manual Request"
