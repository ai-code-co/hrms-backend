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


def format_seconds_to_iso_duration(seconds):
    """Convert seconds to ISO 8601 duration format like 'PT09H00M00S'"""
    if seconds is None or seconds == 0:
        return "PT00H00M00S"
    
    hours = abs(seconds) // 3600
    minutes = (abs(seconds) % 3600) // 60
    secs = abs(seconds) % 60
    
    return f"PT{hours:02d}H{minutes:02d}M{secs:02d}S"


def format_seconds_to_hms(seconds, include_sign=False):
    """Convert seconds to HH:MM:SS format with optional sign"""
    if seconds is None:
        return "00:00:00"
    
    sign = ""
    if include_sign:
        sign = "+ " if seconds >= 0 else "- "
        
    abs_seconds = abs(seconds)
    hours = abs_seconds // 3600
    minutes = (abs_seconds % 3600) // 60
    secs = abs_seconds % 60
    
    return f"{sign}{hours:02d}:{minutes:02d}:{secs:02d}"


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


def get_leave_for_date(date, leaves_list):
    """
    Find leave that applies to a specific date.
    Returns: (leave_object, is_rh, is_partial, partial_type)
    """
    for leave in leaves_list:
        if leave.from_date <= date <= leave.to_date:
            # Check if date is a Restricted Holiday
            if leave.rh_dates:
                # Convert all to string for comparison
                rh_date_strings = []
                for d in leave.rh_dates:
                    if isinstance(d, str):
                        rh_date_strings.append(d)
                    else:
                        # Assume date object
                        rh_date_strings.append(str(d))
                
                if str(date) in rh_date_strings:
                    return (leave, True, False, None)
            
            # Check for partial leave
            if leave.day_status:
                return (leave, False, True, leave.day_status)
            
            return (leave, False, False, None)
    return (None, False, False, None)


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
            office_time = format_seconds_to_hms(obj.office_seconds_worked)
            parts.append(f"Office: {office_time}")
        if obj.home_seconds_worked > 0:
            home_time = format_seconds_to_hms(obj.home_seconds_worked)
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
            'seconds_actual_worked_time',
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
        return format_seconds_to_hms(obj.seconds_actual_worked_time)
    
    def get_extra_time(self, obj):
        """Format extra time with status"""
        return format_seconds_to_hms(obj.seconds_extra_time, include_sign=True)
    
    def get_office_time_formatted(self, obj):
        """Format office time worked"""
        return format_seconds_to_hms(obj.office_seconds_worked)
    
    def get_home_time_formatted(self, obj):
        """Format home time worked"""
        return format_seconds_to_hms(obj.home_seconds_worked)
    
    def get_work_location_summary(self, obj):
        """Get summary of work locations and times"""
        parts = []
        if obj.office_seconds_worked > 0:
            office_time = format_seconds_to_hms(obj.office_seconds_worked)
            parts.append(f"Office: {office_time}")
        if obj.home_seconds_worked > 0:
            home_time = format_seconds_to_hms(obj.home_seconds_worked)
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
            'is_working_from_home'
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
    def serialize_monthly_data(attendance_records, employee, month, year, holidays_list, leaves_list):
        """Create monthly attendance data structure matching API format"""
        from django.utils import timezone
        from holidays.models import Holiday
        from leaves.models import Leave
        
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
        
        # Counters for the summary
        working_days_count = 0
        non_working_days_count = 0
        leave_days_count = 0
        half_days_count = 0
        
        for day in range(1, num_days + 1):
            current_date = datetime(year, month, day).date()
            day_name = current_date.strftime(DAY_NAME_FORMAT)
            is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6
            is_holiday = current_date in holiday_dates
            is_future = current_date > today
            is_before_joining = employee.joining_date and current_date < employee.joining_date
            
            # Get attendance record if exists
            attendance = attendance_map.get(current_date)
            
            # Get leave info for current date
            leave_info = get_leave_for_date(current_date, leaves_list)
            leave, is_rh, is_partial, partial_type = leave_info
            
            # Determine day type
            if is_before_joining:
                day_type = "BEFORE_JOINING"
                non_working_days_count += 1
            elif is_holiday or is_weekend:
                day_type = "NON_WORKING_DAY"
                non_working_days_count += 1
            elif leave:
                leave_status = getattr(leave, 'status', '')
                if leave_status in ['Approved', 'APPROVED']:
                    if is_partial:
                        day_type = "WORKING_DAY"
                        half_days_count += 1
                        working_days_count += 1
                    else:
                        day_type = "LEAVE_DAY"
                        leave_days_count += 1
                else:
                    # If leave is pending/rejected, it's still a working day or absent
                    if is_future:
                        day_type = "FUTURE_DAY"
                        working_days_count += 1
                    elif attendance and ((attendance.office_in_time and attendance.office_out_time) or (attendance.home_in_time and attendance.home_out_time)):
                        day_type = "WORKING_DAY"
                        working_days_count += 1
                    else:
                        day_type = "ABSENT" if not is_future else "FUTURE_DAY"
                        working_days_count += 1
            elif is_future:
                day_type = "FUTURE_DAY"
                working_days_count += 1
            elif attendance and ((attendance.office_in_time and attendance.office_out_time) or (attendance.home_in_time and attendance.home_out_time)):
                day_type = "WORKING_DAY"
                working_days_count += 1
            else:
                # Past day with no check-in and no leave
                day_type = "ABSENT"
                working_days_count += 1
            
            # Default working hours
            default_office_hours = getattr(settings, 'ATTENDANCE_DEFAULT_WORKING_HOURS', '09:00')
            default_total_time = getattr(settings, 'ATTENDANCE_DEFAULT_TOTAL_TIME_SECONDS', 32400)
            
            if attendance:
                office_hours = attendance.office_working_hours or default_office_hours
                total_time = attendance.orignal_total_time or default_total_time
                office_in_time_str = format_datetime_to_iso(attendance.office_in_time) if attendance.office_in_time else ""
                office_out_time_str = format_datetime_to_iso(attendance.office_out_time) if attendance.office_out_time else ""
                home_in_time_str = format_datetime_to_iso(attendance.home_in_time) if attendance.home_in_time else ""
                home_out_time_str = format_datetime_to_iso(attendance.home_out_time) if attendance.home_out_time else ""
                total_time_str = format_seconds_to_hms(attendance.seconds_actual_worked_time)
                extra_time_str = format_seconds_to_hms(attendance.seconds_extra_time, include_sign=True)
                
                timesheet_status = getattr(attendance, 'timesheet_status', None)
                if timesheet_status is None or timesheet_status == 'APPROVED':
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
            
            # File and status
            file_url = ""
            file_id = ""
            if attendance and hasattr(attendance, 'tracker_screenshot') and attendance.tracker_screenshot:
                try: file_url = attendance.tracker_screenshot.url
                except: file_url = ""
                file_id = str(attendance.id)
            
            status = attendance.get_timesheet_status_display() if attendance and hasattr(attendance, 'timesheet_status') else ""
            comments = attendance.text or attendance.day_text or "" if attendance else ""
            
            # Day text priority: Holiday name > Leave reason > Check-in notes
            day_text = ""
            if is_holiday: day_text = holiday_dates.get(current_date, "")
            elif leave: day_text = leave.reason
            elif attendance: day_text = attendance.day_text or attendance.text
            
            day_record = {
                "full_date": current_date.strftime("%Y-%m-%d"),
                "date": f"{day:02d}",
                "day": day_name,
                "office_working_hours": office_hours,
                "day_type": day_type,
                "day_text": day_text,
                "in_time": office_in_time_str or home_in_time_str,
                "out_time": office_out_time_str or home_out_time_str,
                "total_time": total_time_str,
                "extra_time": extra_time_str,
                "text": comments,
                "admin_alert": 0, # Simplified for now
                "admin_alert_message": "",
                "orignal_total_time": total_time,
                "isDayBeforeJoining": is_before_joining,
                "status": status,
                "leave_id": leave.id if leave else None,
                "leave_type": leave.leave_type if leave else "",
                "is_restricted_holiday": is_rh,
                "is_partial_leave": is_partial
            }
            attendance_array.append(day_record)
        
        # Calculate summaries with "Till Today" logic
        compensation_time_str = format_seconds_to_hms(seconds_to_compensate)
        actual_working_hours = format_seconds_to_hours_mins(total_seconds_worked)
        
        calculation_limit_date = today if (year == today.year and month == today.month) else datetime(year, month, num_days).date()
        total_working_days_expected = 0.0
        
        for day in range(1, num_days + 1):
            current_date = datetime(year, month, day).date()
            if current_date > calculation_limit_date:
                continue
                
            is_weekend = current_date.weekday() >= 5
            is_holiday = current_date in holiday_dates
            is_before_joining = employee.joining_date and current_date < employee.joining_date
            
            if is_before_joining or is_weekend or is_holiday:
                continue
            
            l_info = get_leave_for_date(current_date, leaves_list)
            l, i_rh, i_partial, p_type = l_info
            l_status = getattr(l, 'status', '') if l else ''
            
            if l and l_status in ['Approved', 'APPROVED']:
                if i_partial: total_working_days_expected += 0.5
                elif i_rh: total_working_days_expected += 1.0
                # Full day leave = 0 hours expected
            else:
                total_working_days_expected += 1.0
        
        total_expected_seconds = int(total_working_days_expected * default_total_time)
        total_working_hours = format_seconds_to_hms(total_expected_seconds)
        actual_working_hours_formatted = format_seconds_to_hms(total_seconds_worked)
        
        pending_seconds = total_expected_seconds - total_seconds_worked
        pending_sign = "+ " if pending_seconds >= 0 else "- "
        pending_working_hours = f"{pending_sign}{format_seconds_to_hms(abs(pending_seconds))}"

        # Month Navigation
        if month == 12: next_month, next_year = 1, year + 1
        else: next_month, next_year = month + 1, year
        if month == 1: prev_month, prev_year = 12, year - 1
        else: prev_month, prev_year = month - 1, year
        
        month_names = [formats.date_format(datetime(year, m, 1).date(), 'F') for m in range(1, 13)]
        
        data = {
            "userProfileImage": "",
            "userName": employee.get_full_name(),
            "userjobtitle": employee.designation.name if employee.designation else "",
            "userid": str(employee.id),
            "year": year,
            "month": month,
            "monthName": month_names[month - 1],
            "monthSummary": {
                "actual_working_hours": actual_working_hours_formatted,
                "completed_working_hours": actual_working_hours_formatted,
                "pending_working_hours": pending_working_hours,
                "total_working_hours": total_working_hours,
                "WORKING_DAY": working_days_count,
                "NON_WORKING_DAY": non_working_days_count,
                "LEAVE_DAY": leave_days_count,
                "HALF_DAY": half_days_count,
                "admin_alert": "",
                "admin_alert_message": "",
                "seconds_actual_working_hours": total_expected_seconds,
                "seconds_completed_working_hours": total_seconds_worked,
                "seconds_pending_working_hours": pending_seconds
            },
            "attendance": attendance_array,
            "compensationSummary": {
                "seconds_to_be_compensate": seconds_to_compensate,
                "time_to_be_compensate": compensation_time_str
            },
            "nextMonth": {"year": str(next_year), "month": f"{next_month:02d}", "monthName": month_names[next_month - 1]},
            "previousMonth": {"year": str(prev_year), "month": f"{prev_month:02d}", "monthName": month_names[prev_month - 1]},
            "error": 0
        }
        return {"error": 0, "data": data}


class WeeklyTimesheetSubmitSerializer(serializers.Serializer):
    """Serializer for submitting weekly timesheet entries"""
    date = serializers.DateField(required=True)
    total_time = serializers.CharField(required=True, help_text="Total hours worked (e.g., '8', '8.5')")
    comments = serializers.CharField(required=False, allow_blank=True, help_text="Comments/work description (required for WFH)")
    tracker_screenshot = serializers.FileField(required=False, allow_null=True, help_text="Tracker screenshot (required for WFH)")
    is_working_from_home = serializers.BooleanField(default=False)
    home_in_time = serializers.CharField(required=False, allow_blank=True, help_text="Home check-in time in 12-hour format (e.g., '10:30 AM') - optional")
    home_out_time = serializers.CharField(required=False, allow_blank=True, help_text="Home check-out time in 12-hour format (e.g., '06:30 PM') - optional")
    
    def validate_date(self, value):
        """Validate date is not weekend or holiday"""
        from holidays.models import Holiday
        
        # Check if date is weekend
        if value.weekday() >= 5:  # Saturday=5, Sunday=6
            raise serializers.ValidationError("Cannot submit timesheet for weekends.")
        
        # Check if date is a holiday
        if Holiday.objects.filter(date=value, is_active=True).exists():
            holiday = Holiday.objects.get(date=value, is_active=True)
            raise serializers.ValidationError(f"Cannot submit timesheet for holiday: {holiday.name}")
        
        return value
    
    def validate(self, data):
        """Validate WFH requirements and resubmission rules"""
        is_wfh = data.get('is_working_from_home', False)
        comments = data.get('comments', '').strip()
        screenshot = data.get('tracker_screenshot')
        date = data.get('date')
        
        # Check for existing attendance record
        if date:
            from .models import Attendance
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get employee from request context (will be set in view)
            employee = self.context.get('employee')
            if employee:
                existing = Attendance.objects.filter(
                    employee=employee,
                    date=date
                ).first()
                
                if existing:
                    # Check timesheet status safely (only if field exists)
                    if hasattr(existing, 'timesheet_status') and existing.timesheet_status in ['PENDING', 'APPROVED']:
                        status_display = existing.get_timesheet_status_display() if hasattr(existing, 'get_timesheet_status_display') else existing.timesheet_status
                        raise serializers.ValidationError({
                            'date': 'Timesheet already submitted for this date. Status: {}'.format(status_display)
                        })
                    # Allow resubmission if status is REJECTED or if timesheet_status field doesn't exist
        
        # WFH validation
        if is_wfh:
            errors = {}
            
            # Comments required (min 20 chars)
            if not comments or len(comments) < 20:
                errors['comments'] = 'Valid work description (minimum 20 characters) is required when working from home. Please describe what work was done that day.'
            
            # Screenshot required
            if not screenshot:
                errors['tracker_screenshot'] = 'Tracker screenshot is required when working from home.'
            else:
                # Validate file type
                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf']
                if screenshot.content_type not in allowed_types:
                    errors['tracker_screenshot'] = 'Invalid file type. Allowed: JPG, PNG, GIF, WEBP, PDF'
                
                # Validate file size (5MB max)
                if screenshot.size > 5 * 1024 * 1024:
                    errors['tracker_screenshot'] = 'File size exceeds 5MB limit.'
            
            if errors:
                raise serializers.ValidationError(errors)
        
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


class WeeklyTimesheetSerializer(serializers.Serializer):
    """Serializer for weekly timesheet GET response"""
    
    @staticmethod
    def serialize_weekly_data(attendance_records, employee, week_start_date):
        """Create weekly attendance data structure matching API format"""
        from django.utils import timezone
        from holidays.models import Holiday
        from datetime import timedelta
        
        # Calculate week range (Monday to Sunday)
        # week_start_date should be Monday
        week_days = []
        for i in range(7):
            current_date = week_start_date + timedelta(days=i)
            week_days.append(current_date)
        
        today = timezone.now().date()
        
        # Get holidays for the week
        week_holidays = Holiday.objects.filter(
            date__gte=week_days[0],
            date__lte=week_days[6],
            is_active=True
        ).values_list('date', 'name')
        holiday_dates = {h[0]: h[1] for h in week_holidays}
        
        # Create attendance map
        attendance_map = {rec.date: rec for rec in attendance_records}
        
        # Build attendance array for all 7 days
        attendance_array = []
        
        for current_date in week_days:
            day_name = current_date.strftime(DAY_NAME_FORMAT)
            is_weekend = current_date.weekday() >= 5
            is_holiday = current_date in holiday_dates
            is_future = current_date > today
            
            # Get attendance record if exists
            attendance = attendance_map.get(current_date)
            
            # Determine day type
            if is_holiday:
                day_type = "HOLIDAY"
            elif is_weekend:
                day_type = "WEEKEND_OFF"
            elif is_future:
                day_type = "WORKING_DAY"
            elif attendance:
                day_type = getattr(attendance, 'day_type', 'WORKING_DAY')
            else:
                day_type = "WORKING_DAY"
            
            # Default office working hours
            default_office_hours = getattr(settings, 'ATTENDANCE_DEFAULT_WORKING_HOURS', '09:00')
            default_total_time = getattr(settings, 'ATTENDANCE_DEFAULT_TOTAL_TIME_SECONDS', 32400)
            
            if attendance:
                office_hours = getattr(attendance, 'office_working_hours', None) or default_office_hours
                total_time = getattr(attendance, 'orignal_total_time', None) or default_total_time
                
                # Format times
                home_in_time = getattr(attendance, 'home_in_time', None)
                office_in_time = getattr(attendance, 'office_in_time', None)
                home_out_time = getattr(attendance, 'home_out_time', None)
                office_out_time = getattr(attendance, 'office_out_time', None)
                
                in_time_str = format_datetime_to_iso(home_in_time) if home_in_time else format_datetime_to_iso(office_in_time) if office_in_time else ""
                out_time_str = format_datetime_to_iso(home_out_time) if home_out_time else format_datetime_to_iso(office_out_time) if office_out_time else ""
                
                # Calculate total and extra time
                seconds_worked = getattr(attendance, 'seconds_actual_worked_time', 0) or 0
                total_time_str = format_seconds_to_hms(seconds_worked)
                
                seconds_extra = getattr(attendance, 'seconds_extra_time', 0) or 0
                extra_time_str = format_seconds_to_hms(seconds_extra, include_sign=True)
                
                # File URL - safely check for tracker_screenshot field
                file_url = ""
                file_id = ""
                if hasattr(attendance, 'tracker_screenshot') and attendance.tracker_screenshot:
                    try:
                        file_url = attendance.tracker_screenshot.url
                    except (AttributeError, ValueError):
                        file_url = ""
                    file_id = str(attendance.id)
                
                # Status - safely check for timesheet_status field
                status = ""
                if hasattr(attendance, 'timesheet_status') and hasattr(attendance, 'get_timesheet_status_display'):
                    try:
                        status = attendance.get_timesheet_status_display()
                    except (AttributeError, ValueError):
                        status = ""
                
                # Comments
                text = getattr(attendance, 'text', '') or ''
                day_text = getattr(attendance, 'day_text', '') or ''
                comments = text or day_text or ""
            else:
                office_hours = default_office_hours
                total_time = default_total_time
                in_time_str = ""
                out_time_str = ""
                total_time_str = "00:00:00"
                extra_time_str = "00:00:00"
                file_url = ""
                file_id = ""
                status = ""
                comments = ""
            
            # Build day record
            day_record = {
                "full_date": current_date.strftime(DATE_FORMAT),
                "date": current_date.strftime(DAY_NUMBER_FORMAT),
                "day": day_name,
                "office_working_hours": office_hours,
                "total_hours": total_time_str,
                "total_time": total_time_str,
                "extra_time": extra_time_str,
                "comments": comments,
                "file": file_url,
                "fileId": file_id,
                "status": status,
                "is_working_from_home": getattr(attendance, 'is_working_from_home', False) if attendance else False,
                "in_time": in_time_str,
                "out_time": out_time_str,
                "day_type": day_type,
                "admin_alert": getattr(attendance, 'admin_alert', 0) if attendance else (0 if is_future or is_holiday or is_weekend else 1),
                "admin_alert_message": getattr(attendance, 'admin_alert_message', "") if attendance else ("" if is_future or is_holiday or is_weekend else ADMIN_ALERT_MESSAGE_MISSING_TIME),
            }
            
            attendance_array.append(day_record)
        
        return {
            "error": 0,
            "data": attendance_array
        }
