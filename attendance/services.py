from django.utils import timezone
from django.conf import settings


class AttendanceCalculationService:

    @staticmethod
    def calculate_worked_seconds(in_time, out_time):
        if not (in_time and out_time):
            return 0
        return int((out_time - in_time).total_seconds())

    @staticmethod
    def calculate_location_seconds(in_time, out_time):
        if not (in_time and out_time):
            return 0
        return int((out_time - in_time).total_seconds())

    @staticmethod
    def get_earliest_checkin(attendance):
        times = [t for t in [
            attendance.office_in_time,
            attendance.home_in_time,
            attendance.in_time
        ] if t]
        return min(times) if times else None

    @staticmethod
    def get_latest_checkout(attendance):
        times = [t for t in [
            attendance.office_out_time,
            attendance.home_out_time,
            attendance.out_time
        ] if t]
        return max(times) if times else None

    @staticmethod
    def calculate_total_worked_seconds(attendance):
        return (
            AttendanceCalculationService.calculate_location_seconds(
                attendance.office_in_time, attendance.office_out_time
            ) +
            AttendanceCalculationService.calculate_location_seconds(
                attendance.home_in_time, attendance.home_out_time
            )
        )

    @staticmethod
    def calculate_extra_seconds(worked, scheduled):
        return worked - scheduled

    @staticmethod
    def extra_time_status(extra):
        if extra > 0:
            return '+'
        if extra < 0:
            return '-'
        return ''

    @staticmethod
    def should_flag_admin_alert(attendance):
        if attendance.day_type in ['HOLIDAY', 'WEEKEND_OFF', 'LEAVE_DAY']:
            return False

        if attendance.office_in_time and not attendance.office_out_time:
            return True
        if attendance.home_in_time and not attendance.home_out_time:
            return True

        return not (attendance.in_time and attendance.out_time)

    @staticmethod
    def determine_day_type(attendance, today=None):
        """
        Determines the day_type for an attendance record based on date, holidays, 
        and weekends.
        """
        if not today:
            today = timezone.now().date()
            
        date = attendance.date
        
        # Check if date is before joining
        if attendance.employee.joining_date and date < attendance.employee.joining_date:
            attendance.day_type = 'BEFORE_JOINING'
            return

        # Check for future dates
        if date > today:
            attendance.day_type = 'FUTURE_DAY'
            return

        # Check for weekends
        if date.weekday() >= 5: # Saturday=5, Sunday=6
            attendance.day_type = 'WEEKEND_OFF'
            return

        # Check for holidays
        from holidays.models import Holiday
        if Holiday.objects.filter(date=date, is_active=True).exists():
            attendance.day_type = 'HOLIDAY'
            return
        
        # Check for leaves
        from leaves.models import Leave
        leave = Leave.objects.filter(
            employee=attendance.employee,
            from_date__lte=date,
            to_date__gte=date,
            status='APPROVED'
        ).first()
        
        if leave:
            attendance.day_type = 'LEAVE_DAY'
            return

        # If has work time recorded
        if (attendance.in_time and attendance.out_time) or \
           (attendance.office_in_time and attendance.office_out_time) or \
           (attendance.home_in_time and attendance.home_out_time):
            attendance.day_type = 'WORKING_DAY'
            return

        # Default for past working days with no activity
        if date < today:
            attendance.day_type = 'ABSENT'
        else:
            attendance.day_type = 'WORKING_DAY'
