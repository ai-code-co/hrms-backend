from rest_framework import serializers
from .models import Attendance
from datetime import datetime
from calendar import monthrange
from django.conf import settings
from django.utils import formats
from .constants import (
    DATE_FORMAT, TIME_12HR_FORMAT, DAY_NAME_FORMAT, DAY_NUMBER_FORMAT,
    DATETIME_ISO_FORMAT, ADMIN_ALERT_MESSAGE_MISSING_TIME
)


def format_seconds_to_time(seconds):
    """Convert seconds to formatted string like '9h : 21m :30s'"""
    if seconds is None or seconds == 0:
        return ""
    
    hours = abs(seconds) // 3600
    minutes = (abs(seconds) % 3600) // 60
    secs = abs(seconds) % 60
    
    if hours > 0:
        return f"{hours}h : {minutes}m :{secs}s"
    elif minutes > 0:
        return f"{minutes}m :{secs}s"
    else:
        return f"{secs}s"


def format_seconds_to_hours_mins(seconds):
    """Convert seconds to formatted string like '210 Hrs 53 Mins'"""
    if seconds is None or seconds == 0:
        return "0 Hrs 0 Mins"
    
    hours = abs(seconds) // 3600
    minutes = (abs(seconds) % 3600) // 60
    
    return f"{hours} Hrs {minutes} Mins"


def format_time_to_12hr(dt):
    """Convert datetime to 12-hour format like '10:23 AM'"""
    if dt is None:
        return ""
    return dt.strftime(TIME_12HR_FORMAT)


def format_datetime_to_iso(dt):
    """Convert datetime to ISO 8601 format with timezone like '2025-12-01T07:17:00Z'"""
    if dt is None:
        return ""
    from django.utils import timezone
    from datetime import timezone as dt_timezone
    
    # Convert to UTC
    if timezone.is_aware(dt):
        dt_utc = dt.astimezone(dt_timezone.utc)
    else:
        # Make aware in current timezone, then convert to UTC
        dt_aware = timezone.make_aware(dt, timezone.get_current_timezone())
        dt_utc = dt_aware.astimezone(dt_timezone.utc)
    
    return dt_utc.strftime(DATETIME_ISO_FORMAT)


class AttendanceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for attendance lists"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    work_location_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_id', 'employee_name', 'date',
            'day_type', 'admin_alert',
            'seconds_actual_worked_time', 'seconds_extra_time',
            'office_in_time', 'office_out_time', 'home_in_time', 'home_out_time',
            'office_seconds_worked', 'home_seconds_worked', 'work_location_summary',
            'is_working_from_home'
        ]
    
    def get_work_location_summary(self, obj):
        """Get summary of work locations and times"""
        parts = []
        if obj.office_seconds_worked > 0:
            office_time = format_seconds_to_time(obj.office_seconds_worked)
            parts.append(f"Office: {office_time}")
        if obj.home_seconds_worked > 0:
            home_time = format_seconds_to_time(obj.home_seconds_worked)
            parts.append(f"Home: {home_time}")
        return ", ".join(parts) if parts else ""


class AttendanceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer matching API response format"""
    # Computed date fields
    full_date = serializers.SerializerMethodField()
    date_str = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()
    
    # Formatted time strings
    total_time = serializers.SerializerMethodField()
    extra_time = serializers.SerializerMethodField()
    office_time_formatted = serializers.SerializerMethodField()
    home_time_formatted = serializers.SerializerMethodField()
    work_location_summary = serializers.SerializerMethodField()
    
    # Employee info
    employee_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            # Date fields
            'full_date', 'date_str', 'day', 'date',
            # Location-specific times
            'office_in_time', 'office_out_time', 'home_in_time', 'home_out_time',
            # Working hours
            'office_working_hours', 'orignal_total_time',
            # Calculated time (seconds)
            'seconds_actual_worked_time', 'seconds_actual_working_time',
            'seconds_extra_time', 'office_time_inside',
            'office_seconds_worked', 'home_seconds_worked',
            # Formatted time strings
            'total_time', 'extra_time', 'office_time_formatted', 'home_time_formatted',
            'work_location_summary',
            # Status
            'day_type', 'extra_time_status',
            # Alerts
            'admin_alert', 'admin_alert_message',
            # Messages
            'day_text', 'text',
            # Flags
            'is_working_from_home',
            # Employee
            'employee', 'employee_detail',
            # System
            'id', 'created_at', 'updated_at'
        ]
    
    def get_full_date(self, obj):
        """Return full date as YYYY-MM-DD"""
        return obj.date.strftime(DATE_FORMAT)
    
    def get_date_str(self, obj):
        """Return day number as string"""
        return obj.date.strftime(DAY_NUMBER_FORMAT)
    
    def get_day(self, obj):
        """Return day name"""
        return obj.date.strftime(DAY_NAME_FORMAT)
    
    def get_total_time(self, obj):
        """Format total time worked"""
        return format_seconds_to_time(obj.seconds_actual_worked_time)
    
    def get_extra_time(self, obj):
        """Format extra time with status"""
        if obj.seconds_extra_time == 0:
            return ""
        return format_seconds_to_time(obj.seconds_extra_time)
    
    def get_office_time_formatted(self, obj):
        """Format office time worked"""
        return format_seconds_to_time(obj.office_seconds_worked)
    
    def get_home_time_formatted(self, obj):
        """Format home time worked"""
        return format_seconds_to_time(obj.home_seconds_worked)
    
    def get_work_location_summary(self, obj):
        """Get summary of work locations and times"""
        parts = []
        if obj.office_seconds_worked > 0:
            office_time = format_seconds_to_time(obj.office_seconds_worked)
            parts.append(f"Office: {office_time}")
        if obj.home_seconds_worked > 0:
            home_time = format_seconds_to_time(obj.home_seconds_worked)
            parts.append(f"Home: {home_time}")
        return ", ".join(parts) if parts else ""
    
    def get_employee_detail(self, obj):
        """Get employee details"""
        return {
            'id': obj.employee.id,
            'employee_id': obj.employee.employee_id,
            'full_name': obj.employee.get_full_name(),
            'email': obj.employee.email,
            'designation': obj.employee.designation.name if obj.employee.designation else None,
            'department': obj.employee.department.name if obj.employee.department else None,
        }


class AttendanceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating attendance records"""
    
    class Meta:
        model = Attendance
        fields = [
            'employee', 'date', 'in_time', 'out_time',
            'office_in_time', 'office_out_time', 'home_in_time', 'home_out_time',
            'office_working_hours', 'orignal_total_time',
            'day_type', 'day_text', 'text',
            'is_day_before_joining', 'is_working_from_home'
        ]
    
    def validate(self, data):
        """Validate attendance data"""
        if data.get('out_time') and data.get('in_time'):
            if data['out_time'] < data['in_time']:
                raise serializers.ValidationError("Check-out time cannot be before check-in time.")
        return data


class CheckInSerializer(serializers.Serializer):
    """Serializer for check-in action"""
    date = serializers.DateField(required=False, help_text="Date for check-in (defaults to today)")
    location = serializers.ChoiceField(
        choices=['OFFICE', 'HOME'],
        required=False,
        help_text="Work location: OFFICE or HOME (not required if is_work_from_home is true)"
    )
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional notes")
    is_work_from_home = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Mark as working from home"
    )
    is_working_from_home = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Mark as working from home (alias for is_work_from_home)"
    )
    check_in = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Check-in time in 12-hour format (e.g., '12:00 PM') - used when working from home (deprecated, use home_check_in)"
    )
    check_out = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Check-out time in 12-hour format (e.g., '09:30 PM') - used when working from home (deprecated, use home_check_out)"
    )
    home_check_in = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Home check-in time in 12-hour format (e.g., '12:00 PM') - used when working from home"
    )
    home_check_out = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Home check-out time in 12-hour format (e.g., '09:30 PM') - used when working from home"
    )
    
    def validate_date(self, value):
        """Validate date is not in the future"""
        from django.utils import timezone
        today = timezone.now().date()
        if value > today:
            raise serializers.ValidationError("Cannot check-in for a future date.")
        return value
    
    def validate(self, data):
        """Validate that location or is_work_from_home is provided"""
        is_work_from_home = data.get('is_work_from_home', False) or data.get('is_working_from_home', False)
        location = data.get('location')
        # Support both old and new field names
        check_in = data.get('home_check_in', '') or data.get('check_in', '')
        check_out = data.get('home_check_out', '') or data.get('check_out', '')
        notes = data.get('notes', '')
        date = data.get('date')
        
        # If working from home, validate required fields
        if is_work_from_home:
            errors = {}
            
            # Date is required
            if not date:
                errors['date'] = "Date is required when working from home."
            
            # Check-in time is required
            if not check_in:
                errors['home_check_in'] = "Home check-in time is required when working from home."
            
            # Check-out time is required
            if not check_out:
                errors['home_check_out'] = "Home check-out time is required when working from home."
            
            # Notes (reason) is required
            if not notes or not notes.strip():
                errors['notes'] = "Reason is required when working from home."
            
            if errors:
                raise serializers.ValidationError(errors)
            
            # Store the values with the new field names for consistency
            if data.get('check_in') and not data.get('home_check_in'):
                data['home_check_in'] = data['check_in']
            if data.get('check_out') and not data.get('home_check_out'):
                data['home_check_out'] = data['check_out']
            
            return data
        
        # If not working from home, location is required
        if not location:
            raise serializers.ValidationError({
                "location": "Location is required when not working from home."
            })
        
        return data
    
    def parse_time_string(self, time_str, date):
        """Parse time string like '12:00 PM' to datetime"""
        from django.utils import timezone
        from datetime import datetime
        import re
        
        if not time_str:
            return None
        
        # Parse 12-hour format: "12:00 PM" or "09:30 PM"
        time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM)'
        match = re.match(time_pattern, time_str.strip(), re.IGNORECASE)
        
        if not match:
            raise serializers.ValidationError(f"Invalid time format: {time_str}. Use format like '12:00 PM'")
        
        hour = int(match.group(1))
        minute = int(match.group(2))
        am_pm = match.group(3).upper()
        
        # Convert to 24-hour format
        if am_pm == 'PM' and hour != 12:
            hour += 12
        elif am_pm == 'AM' and hour == 12:
            hour = 0
        
        # Create datetime with the provided date
        dt = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
        return timezone.make_aware(dt)


class CheckOutSerializer(serializers.Serializer):
    """Serializer for check-out action"""
    date = serializers.DateField(required=False, help_text="Date for check-out (defaults to today)")
    location = serializers.ChoiceField(
        choices=['OFFICE', 'HOME'],
        required=True,
        help_text="Work location: OFFICE or HOME"
    )
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional notes")
    
    def validate_date(self, value):
        """Validate date is not in the future"""
        from django.utils import timezone
        today = timezone.now().date()
        if value > today:
            raise serializers.ValidationError("Cannot check-out for a future date.")
        return value


class MonthlyAttendanceSerializer(serializers.Serializer):
    """Serializer for monthly attendance summary response"""
    error = serializers.IntegerField(default=0)
    data = serializers.DictField()
    
    @staticmethod
    def serialize_monthly_data(attendance_records, employee, month, year, holidays_list):
        """Create monthly attendance data structure matching API format"""
        from django.utils import timezone
        from holidays.models import Holiday
        
        # Get all days in the month
        num_days = monthrange(year, month)[1]
        today = timezone.now().date()
        
        # Get holidays for the month
        month_holidays = Holiday.objects.filter(
            date__year=year,
            date__month=month,
            is_active=True
        ).values_list('date', 'name')
        holiday_dates = {h[0]: h[1] for h in month_holidays}
        
        # Create attendance map
        attendance_map = {rec.date: rec for rec in attendance_records}
        
        # Build attendance array for all days in month
        attendance_array = []
        total_seconds_worked = 0
        total_seconds_extra = 0
        seconds_to_compensate = 0
        
        for day in range(1, num_days + 1):
            current_date = datetime(year, month, day).date()
            day_name = current_date.strftime(DAY_NAME_FORMAT)
            is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6
            is_holiday = current_date in holiday_dates
            is_future = current_date > today
            is_before_joining = employee.joining_date and current_date < employee.joining_date
            
            # Get attendance record if exists
            attendance = attendance_map.get(current_date)
            
            # Determine day type
            if is_before_joining:
                day_type = "WORKING_DAY"  # Can be customized
            elif is_holiday:
                day_type = "HOLIDAY"
            elif is_weekend:
                day_type = "WEEKEND_OFF"
            elif is_future:
                day_type = "WORKING_DAY"  # FUTURE_WORKING_DAY removed
            elif attendance and ((attendance.office_in_time and attendance.office_out_time) or (attendance.home_in_time and attendance.home_out_time)):
                day_type = "WORKING_DAY"
            else:
                day_type = "WORKING_DAY"
            
            # Default office working hours from settings
            default_office_hours = getattr(settings, 'ATTENDANCE_DEFAULT_WORKING_HOURS', '09:00')
            default_total_time = getattr(settings, 'ATTENDANCE_DEFAULT_TOTAL_TIME_SECONDS', 32400)
            
            if attendance:
                office_hours = attendance.office_working_hours or default_office_hours
                total_time = attendance.orignal_total_time or default_total_time
                office_in_time_str = format_datetime_to_iso(attendance.office_in_time) if attendance.office_in_time else ""
                office_out_time_str = format_datetime_to_iso(attendance.office_out_time) if attendance.office_out_time else ""
                home_in_time_str = format_datetime_to_iso(attendance.home_in_time) if attendance.home_in_time else ""
                home_out_time_str = format_datetime_to_iso(attendance.home_out_time) if attendance.home_out_time else ""
                total_time_str = format_seconds_to_time(attendance.seconds_actual_worked_time)
                extra_time_str = format_seconds_to_time(attendance.seconds_extra_time)
                
                total_seconds_worked += attendance.seconds_actual_worked_time
                total_seconds_extra += attendance.seconds_extra_time
                
                if attendance.seconds_extra_time < 0:
                    seconds_to_compensate += abs(attendance.seconds_extra_time)
            else:
                office_hours = default_office_hours
                total_time = default_total_time
                office_in_time_str = ""
                office_out_time_str = ""
                home_in_time_str = ""
                home_out_time_str = ""
                total_time_str = ""
                extra_time_str = ""
            
            # Build day record
            day_record = {
                "date": current_date.strftime(DATE_FORMAT),
                "day": day_name,
                "office_working_hours": office_hours,
                "admin_alert": 1 if (not attendance or not ((attendance.office_in_time and attendance.office_out_time) or (attendance.home_in_time and attendance.home_out_time))) and not is_future and not is_holiday and not is_weekend else 0,
                "admin_alert_message": ADMIN_ALERT_MESSAGE_MISSING_TIME if (not attendance or not ((attendance.office_in_time and attendance.office_out_time) or (attendance.home_in_time and attendance.home_out_time))) and not is_future and not is_holiday and not is_weekend else "",
                "day_text": attendance.day_text if attendance else "",
                "day_type": day_type,
                "extra_time": extra_time_str,
                "extra_time_status": attendance.extra_time_status if attendance else "",
                "office_in_time": office_in_time_str,
                "office_out_time": office_out_time_str,
                "home_in_time": home_in_time_str,
                "home_out_time": home_out_time_str,
                "is_working_from_home": attendance.is_working_from_home if attendance else False,
                "office_time_inside": attendance.office_time_inside if attendance else 0,
                "orignal_total_time": attendance.orignal_total_time if attendance else total_time,
                "seconds_actual_worked_time": attendance.seconds_actual_worked_time if attendance else 0,
                "seconds_actual_working_time": attendance.seconds_actual_working_time if attendance else 0,
                "seconds_extra_time": attendance.seconds_extra_time if attendance else 0,
                "text": attendance.text if attendance else "",
                "total_time": total_time_str,
            }
            
            attendance_array.append(day_record)
        
        # Calculate summaries
        compensation_time_str = format_seconds_to_time(seconds_to_compensate)
        actual_working_hours = format_seconds_to_hours_mins(total_seconds_worked)
        
        # For completed hours, we might need to calculate based on scheduled hours
        # This is a simplified version - you may need to adjust based on your business logic
        completed_working_hours = format_seconds_to_hours_mins(total_seconds_worked)
        
        # Calculate next and previous month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year
        
        # Use Django's localization for month names
        month_names = []
        for m in range(1, 13):
            # Create a date object for the month and get localized name
            test_date = datetime(year, m, 1).date()
            month_names.append(formats.date_format(test_date, 'F'))
        
        # Build response data
        data = {
            "attendance": attendance_array,
            "compensationSummary": {
                "seconds_to_be_compensate": seconds_to_compensate,
                "time_to_be_compensate": compensation_time_str
            },
            "message": "",
            "month": month,
            "monthName": month_names[month - 1],
            "monthSummary": {
                "actual_working_hours": actual_working_hours,
                "completed_working_hours": completed_working_hours
            },
            "nextMonth": {
                "year": str(next_year),
                "month": f"{next_month:02d}",
                "monthName": month_names[next_month - 1]
            },
            "previousMonth": {
                "year": str(prev_year),
                "month": f"{prev_month:02d}",
                "monthName": month_names[prev_month - 1]
            },
            "userName": employee.get_full_name(),
            "userProfileImage": "",  # You can add profile image URL if available
            "userid": str(employee.id),
            "userjobtitle": employee.designation.name if employee.designation else "",
            "year": year,
            "error": 0
        }
        
        return {
            "error": 0,
            "data": data
        }

