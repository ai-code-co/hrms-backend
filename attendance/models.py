from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from employees.models import Employee
from auth_app.models import User
from .services import AttendanceCalculationService
from .constants import ADMIN_ALERT_MESSAGE_MISSING_TIME


class Attendance(models.Model):
    """Attendance model matching the API structure"""
    
    # Day Type Choices
    DAY_TYPE_CHOICES = [
        ('WORKING_DAY', 'Working Day'),
        ('HALF_DAY', 'Half Day'),
        ('LEAVE_DAY', 'Leave Day'),
        ('HOLIDAY', 'Holiday'),
        ('WEEKEND_OFF', 'Weekend Off'),
    ]
    
    # Extra Time Status Choices
    EXTRA_TIME_STATUS_CHOICES = [
        ('+', 'Overtime'),
        ('-', 'Undertime'),
        ('', 'No Extra Time'),
    ]
    
    # Work Location Choices
    WORK_LOCATION_CHOICES = [
        ('OFFICE', 'Office'),
        ('HOME', 'Home'),
    ]
    
    # Employee relationship
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Employee for this attendance record"
    )
    
    # Date field
    date = models.DateField(
        db_index=True,
        help_text="Attendance date"
    )
    
    # Check-in/Check-out times (kept for backward compatibility)
    in_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Check-in time (calculated from location times)"
    )
    out_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Check-out time (calculated from location times)"
    )
    
    # Location-specific check-in/check-out times
    office_in_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Office check-in time"
    )
    office_out_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Office check-out time"
    )
    home_in_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Home check-in time"
    )
    home_out_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Home check-out time"
    )
    
    # Working hours
    office_working_hours = models.CharField(
        max_length=10,
        default='09:00',  # Default will be overridden in save() if needed
        help_text="Scheduled working hours (e.g., '09:00', '10:38')"
    )
    orignal_total_time = models.IntegerField(
        default=32400,  # Default will be overridden in save() if needed
        help_text="Scheduled total time in seconds (default from settings)"
    )
    
    # Calculated time fields (in seconds)
    seconds_actual_worked_time = models.IntegerField(
        default=0,
        help_text="Actual time worked in seconds"
    )
    seconds_actual_working_time = models.IntegerField(
        default=0,
        help_text="Actual working time in seconds"
    )
    seconds_extra_time = models.IntegerField(
        default=0,
        help_text="Extra/overtime in seconds (can be negative for undertime)"
    )
    office_time_inside = models.IntegerField(
        default=0,
        help_text="Time spent inside office in seconds"
    )
    
    # Location-specific worked time (in seconds)
    office_seconds_worked = models.IntegerField(
        default=0,
        help_text="Time worked at office in seconds"
    )
    home_seconds_worked = models.IntegerField(
        default=0,
        help_text="Time worked at home in seconds"
    )
    
    # Status and type
    day_type = models.CharField(
        max_length=20,
        choices=DAY_TYPE_CHOICES,
        default='WORKING_DAY',
        help_text="Type of day"
    )
    extra_time_status = models.CharField(
        max_length=1,
        choices=EXTRA_TIME_STATUS_CHOICES,
        default='',
        blank=True,
        help_text="Status of extra time (+ for overtime, - for undertime)"
    )
    
    # Alerts and messages
    admin_alert = models.IntegerField(
        default=0,
        help_text="Admin alert flag (0 or 1)"
    )
    admin_alert_message = models.CharField(
        max_length=200,
        blank=True,
        help_text="Admin alert message (e.g., 'In/Out Time Missing')"
    )
    day_text = models.TextField(
        blank=True,
        help_text="Day text message (e.g., 'Previous month pending time merged!!')"
    )
    text = models.TextField(
        blank=True,
        help_text="Additional text field"
    )
    
    # Flags
    is_day_before_joining = models.BooleanField(
        default=False,
        help_text="Is this day before employee joining date"
    )
    is_working_from_home = models.BooleanField(
        default=False,
        help_text="Is employee working from home"
    )
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_attendances'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_attendances'
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
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} ({self.day_type})"
    
    def clean(self):
        """Validate attendance data"""
        from django.utils import timezone

        if self.out_time and self.in_time:
            if self.out_time < self.in_time:
                raise ValidationError("Check-out time cannot be before check-in time.")

        # Validate location-specific times
        if self.office_out_time and self.office_in_time:
            if self.office_out_time < self.office_in_time:
                raise ValidationError("Office check-out time cannot be before office check-in time.")
        
        if self.home_out_time and self.home_in_time:
            if self.home_out_time < self.home_in_time:
                raise ValidationError("Home check-out time cannot be before home check-in time.")

        # Ensure timezone-aware datetimes to avoid incorrect time diff calculations
        if self.in_time and not timezone.is_aware(self.in_time):
            raise ValidationError("Check-in time must be timezone-aware.")
        if self.out_time and not timezone.is_aware(self.out_time):
            raise ValidationError("Check-out time must be timezone-aware.")
        if self.office_in_time and not timezone.is_aware(self.office_in_time):
            raise ValidationError("Office check-in time must be timezone-aware.")
        if self.office_out_time and not timezone.is_aware(self.office_out_time):
            raise ValidationError("Office check-out time must be timezone-aware.")
        if self.home_in_time and not timezone.is_aware(self.home_in_time):
            raise ValidationError("Home check-in time must be timezone-aware.")
        if self.home_out_time and not timezone.is_aware(self.home_out_time):
            raise ValidationError("Home check-out time must be timezone-aware.")
        
        if self.is_day_before_joining and self.employee:
            if self.date >= self.employee.joining_date:
                raise ValidationError("Date cannot be on or after joining date if marked as day before joining.")
    
    def save(self, *args, **kwargs):
        """Override save to calculate time fields and set alerts"""
        # Calculate location-specific worked time
        self.office_seconds_worked = AttendanceCalculationService.calculate_location_seconds(
            self.office_in_time, self.office_out_time
        )
        self.home_seconds_worked = AttendanceCalculationService.calculate_location_seconds(
            self.home_in_time, self.home_out_time
        )
        
        # Calculate total worked time from locations
        total_worked_seconds = AttendanceCalculationService.calculate_total_worked_seconds(self)
        
        # Update backward-compatible in_time and out_time
        earliest_checkin = AttendanceCalculationService.get_earliest_checkin(self)
        latest_checkout = AttendanceCalculationService.get_latest_checkout(self)
        
        if earliest_checkin:
            self.in_time = earliest_checkin
        if latest_checkout:
            self.out_time = latest_checkout
        
        # If location times exist, use them; otherwise fall back to in_time/out_time
        if total_worked_seconds > 0:
            self.seconds_actual_worked_time = total_worked_seconds
            self.seconds_actual_working_time = total_worked_seconds
            self.office_time_inside = self.office_seconds_worked  # Only office time
            self.seconds_extra_time = AttendanceCalculationService.calculate_extra_seconds(
                total_worked_seconds, self.orignal_total_time
            )
            self.extra_time_status = AttendanceCalculationService.extra_time_status(self.seconds_extra_time)
        else:
            # Fallback to old calculation if location times not set
            worked_seconds = AttendanceCalculationService.calculate_worked_seconds(
                self.in_time, self.out_time
            )
            if worked_seconds > 0:
                self.seconds_actual_worked_time = worked_seconds
                self.seconds_actual_working_time = worked_seconds
                self.office_time_inside = worked_seconds
                self.seconds_extra_time = AttendanceCalculationService.calculate_extra_seconds(
                    worked_seconds, self.orignal_total_time
                )
                self.extra_time_status = AttendanceCalculationService.extra_time_status(self.seconds_extra_time)
            else:
                # Reset if times are missing
                self.seconds_actual_worked_time = 0
                self.seconds_actual_working_time = 0
                self.office_time_inside = 0
                self.seconds_extra_time = 0
                self.extra_time_status = ''

        # Set admin alert only for relevant day types
        if AttendanceCalculationService.should_flag_admin_alert(self):
            self.admin_alert = 1
            if not self.admin_alert_message:
                self.admin_alert_message = ADMIN_ALERT_MESSAGE_MISSING_TIME
        else:
            self.admin_alert = 0
            if self.admin_alert_message == ADMIN_ALERT_MESSAGE_MISSING_TIME:
                self.admin_alert_message = ""
        
        self.full_clean()
        super().save(*args, **kwargs)

