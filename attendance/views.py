from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta
from calendar import monthrange

# Optional django-filter import
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False

from .models import Attendance
from .serializers import (
    AttendanceListSerializer,
    AttendanceDetailSerializer,
    AttendanceCreateUpdateSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    MonthlyAttendanceSerializer,
    WeeklyTimesheetSubmitSerializer,
    WeeklyTimesheetSerializer,
    UpdateSessionSerializer
)
from holidays.models import Holiday
from employees.models import Employee
from .services import AttendanceCalculationService
from django.conf import settings
from .constants import DATE_FORMAT, TIME_12HR_FORMAT
from .serializers import format_datetime_to_iso, format_seconds_to_hms


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Attendance management
    
    list: Get all attendance records (filtered by permissions)
    retrieve: Get single attendance details
    create: Create attendance record (Admin only)
    update: Update attendance (Admin only)
    destroy: Delete attendance (Admin only)
    """
    queryset = Attendance.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = [
        'employee', 'date', 'day_type', 'admin_alert'
    ] if HAS_DJANGO_FILTER else []
    search_fields = [
        'employee__first_name', 'employee__last_name', 
        'employee__employee_id', 'date'
    ]
    ordering_fields = ['date', 'in_time', 'out_time', 'created_at']
    ordering = ['-date']
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'list':
            return AttendanceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AttendanceCreateUpdateSerializer
        return AttendanceDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admin/Staff can see all attendance
        if user.is_staff:
            return queryset
        
        # Regular users can only see their own attendance
        if hasattr(user, 'employee_profile'):
            return queryset.filter(employee=user.employee_profile)
        
        return queryset.none()
    
    def get_permissions(self):
        """Set permissions based on action"""
        # Admin-only actions
        admin_actions = ['create', 'update', 'partial_update', 'destroy', 'check_in', 'check_out']
        if self.action in admin_actions:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Set created_by and determine day_type when creating attendance"""
        attendance = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        self._determine_day_type(attendance)
        attendance.save()
    
    def perform_update(self, serializer):
        """Set updated_by and recalculate when updating attendance"""
        attendance = serializer.save(updated_by=self.request.user)
        self._determine_day_type(attendance)
        attendance.save()
    
    def _determine_day_type(self, attendance):
        """Determine day_type based on date, holidays, and weekend"""
        AttendanceCalculationService.determine_day_type(attendance, today=timezone.now().date())
    
    @action(detail=False, methods=['post'], url_path='check-in', permission_classes=[IsAdminUser])
    def check_in(self, request):
        """
        Employee check-in endpoint (Admin/HR only)
        POST /api/attendance/check-in/
        Body: {"date": "2025-12-01", "location": "OFFICE", "notes": "Optional notes"}
        """
        user = request.user
        
        # Check if user has employee profile
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile to check in."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = user.employee_profile
        serializer = CheckInSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "error": 1,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get date and location
        check_date = serializer.validated_data.get('date', timezone.now().date())
        location = serializer.validated_data.get('location')
        notes = serializer.validated_data.get('notes', '')
        is_work_from_home = serializer.validated_data.get('is_work_from_home', False) or serializer.validated_data.get('is_working_from_home', False)
        # Support both old and new field names
        check_in_str = serializer.validated_data.get('home_check_in', '') or serializer.validated_data.get('check_in', '')
        check_out_str = serializer.validated_data.get('home_check_out', '') or serializer.validated_data.get('check_out', '')
        current_time = timezone.now()
        
        # Validate date is not weekend, holiday, or leave day
        # Check if weekend
        if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
            day_name = check_date.strftime('%A')
            return Response({
                "error": 1,
                "message": f"Cannot check-in on weekends. {day_name} is a weekend."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if holiday
        holiday = Holiday.objects.filter(date=check_date, is_active=True).first()
        if holiday:
            return Response({
                "error": 1,
                "message": f"Cannot check-in on holidays. {holiday.name} is a holiday."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if employee has approved leave for this date
        from leaves.models import Leave as LeaveModel
        leave = LeaveModel.objects.filter(
            employee=employee,
            from_date__lte=check_date,
            to_date__gte=check_date,
            status=LeaveModel.Status.APPROVED
        ).first()
        if leave:
            return Response({
                "error": 1,
                "message": f"Cannot check-in on leave days. You have an approved leave from {leave.from_date} to {leave.to_date}."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # If working from home, set location to HOME automatically
        if is_work_from_home:
            location = 'HOME'
        
        # Parse time strings if provided (for work from home)
        home_in_time = None
        home_out_time = None
        
        if is_work_from_home:
            if check_in_str:
                try:
                    home_in_time = serializer.parse_time_string(check_in_str, check_date)
                except Exception as e:
                    return Response({
                        "error": 1,
                        "message": str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # If no check_in time provided, use current time
                home_in_time = current_time
            
            if check_out_str:
                try:
                    home_out_time = serializer.parse_time_string(check_out_str, check_date)
                    # Validate that check_out is after check_in
                    if home_in_time and home_out_time <= home_in_time:
                        return Response({
                            "error": 1,
                            "message": "Check-out time must be after check-in time"
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        "error": 1,
                        "message": str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine if this is a manual entry (work from home with provided times)
        is_manual_entry = is_work_from_home and (check_in_str or check_out_str)
        
        with transaction.atomic():
            # Lock row to prevent concurrent check-ins
            existing = Attendance.objects.select_for_update().filter(
                employee=employee,
                date=check_date
            ).first()

            # Validate location-specific check-in
            if location == 'OFFICE':
                if existing and existing.office_in_time:
                    return Response({
                        "error": 1,
                        "message": f"Already checked in at office for {check_date}"
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif location == 'HOME':
                if existing and existing.home_in_time and not is_work_from_home:
                    return Response({
                        "error": 1,
                        "message": f"Already checked in at home for {check_date}"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set timesheet status based on user role and entry type
            # ALL work-from-home entries from employees need approval, admin entries are auto-approved
            # Regular office check-ins are auto-approved
            if is_work_from_home:
                # Work from home: PENDING for employees, APPROVED for admins
                if user.is_staff or user.is_superuser:
                    timesheet_status = 'APPROVED'
                    timesheet_approved_by = user
                    timesheet_approved_at = timezone.now()
                else:
                    timesheet_status = 'PENDING'
                    timesheet_approved_by = None
                    timesheet_approved_at = None
            else:
                # Regular office check-in: Auto-approved
                timesheet_status = 'APPROVED'
                timesheet_approved_by = user
                timesheet_approved_at = timezone.now()
            
            # Create or update attendance record
            if existing:
                if location == 'OFFICE':
                    existing.office_in_time = current_time
                elif location == 'HOME':
                    if home_in_time:
                        existing.home_in_time = home_in_time
                    else:
                        existing.home_in_time = current_time
                    if home_out_time:
                        existing.home_out_time = home_out_time
                
                existing.is_working_from_home = is_work_from_home
                if notes:
                    existing.day_text = notes
                existing.updated_by = user
                
                # Update timesheet status (only if fields exist in model)
                # For work-from-home entries, always update status
                # For regular check-ins, only update if status is not already set or is PENDING
                if is_work_from_home:
                    if hasattr(existing, 'timesheet_status'):
                        existing.timesheet_status = timesheet_status
                    if hasattr(existing, 'timesheet_submitted_at'):
                        existing.timesheet_submitted_at = timezone.now()
                    if timesheet_approved_by and hasattr(existing, 'timesheet_approved_by'):
                        existing.timesheet_approved_by = timesheet_approved_by
                    if timesheet_approved_at and hasattr(existing, 'timesheet_approved_at'):
                        existing.timesheet_approved_at = timesheet_approved_at
                elif hasattr(existing, 'timesheet_status') and (not existing.timesheet_status or existing.timesheet_status == 'PENDING'):
                    # For regular check-ins, auto-approve if not already set or if pending
                    existing.timesheet_status = timesheet_status
                    if timesheet_approved_by and hasattr(existing, 'timesheet_approved_by'):
                        existing.timesheet_approved_by = timesheet_approved_by
                    if timesheet_approved_at and hasattr(existing, 'timesheet_approved_at'):
                        existing.timesheet_approved_at = timesheet_approved_at
                
                self._determine_day_type(existing)
                existing.save()
                attendance = existing
            else:
                # Create new attendance record
                attendance = Attendance.objects.create(
                    employee=employee,
                    date=check_date,
                    office_in_time=current_time if location == 'OFFICE' else None,
                    home_in_time=home_in_time if location == 'HOME' else (current_time if location == 'HOME' and not home_in_time else None),
                    home_out_time=home_out_time if location == 'HOME' and home_out_time else None,
                    day_text=notes,
                    is_working_from_home=is_work_from_home,
                    office_working_hours=getattr(settings, 'ATTENDANCE_DEFAULT_WORKING_HOURS', '09:00'),
                    orignal_total_time=getattr(settings, 'ATTENDANCE_DEFAULT_TOTAL_TIME_SECONDS', 32400),
                    created_by=user,
                    updated_by=user
                )
                # Set timesheet fields only if they exist in the model
                if hasattr(attendance, 'timesheet_status'):
                    attendance.timesheet_status = timesheet_status
                if is_work_from_home and hasattr(attendance, 'timesheet_submitted_at'):
                    attendance.timesheet_submitted_at = timezone.now()
                if timesheet_status == 'APPROVED':
                    if timesheet_approved_by and hasattr(attendance, 'timesheet_approved_by'):
                        attendance.timesheet_approved_by = timesheet_approved_by
                    if timesheet_approved_at and hasattr(attendance, 'timesheet_approved_at'):
                        attendance.timesheet_approved_at = timesheet_approved_at
                self._determine_day_type(attendance)
                attendance.save()
        
        # Format response
        from .serializers import format_time_to_12hr, format_datetime_to_iso
        
        # Determine if this requires approval (work-from-home from non-admin)
        # ALL work-from-home entries require approval from non-admin users
        requires_approval = is_work_from_home and not (user.is_staff or user.is_superuser)
        
        # Get status display safely
        status_display = ""
        if hasattr(attendance, 'timesheet_status') and hasattr(attendance, 'get_timesheet_status_display'):
            try:
                status_display = attendance.get_timesheet_status_display()
            except (AttributeError, ValueError):
                status_display = getattr(attendance, 'timesheet_status', '')
        elif requires_approval:
            # If timesheet_status field doesn't exist but approval is required, show "Pending"
            status_display = "Pending"
        
        location_time = attendance.office_in_time if location == 'OFFICE' else attendance.home_in_time
        message = "Checked in successfully"
        if is_work_from_home and check_out_str:
            if requires_approval:
                message = "Attendance recorded successfully (check-in and check-out). Pending admin approval."
            else:
                message = "Attendance recorded successfully (check-in and check-out)"
        elif is_work_from_home:
            if requires_approval:
                message = "Checked in successfully at home. Pending admin approval."
            else:
                message = "Checked in successfully at home"
        else:
            message = f"Checked in successfully at {location.lower()}"
        
        return Response({
            "error": 0,
            "data": {
                "message": message,
                "attendance_id": attendance.id,
                "location": location,
                "check_in_time": format_time_to_12hr(location_time),
                "check_out_time": format_time_to_12hr(attendance.home_out_time) if attendance.home_out_time else None,
                "office_in_time": format_datetime_to_iso(attendance.office_in_time) if attendance.office_in_time else None,
                "office_out_time": format_datetime_to_iso(attendance.office_out_time) if attendance.office_out_time else None,
                "home_in_time": format_datetime_to_iso(attendance.home_in_time) if attendance.home_in_time else None,
                "home_out_time": format_datetime_to_iso(attendance.home_out_time) if attendance.home_out_time else None,
                "is_working_from_home": attendance.is_working_from_home,
                "date": attendance.date.strftime(DATE_FORMAT),
                "timesheet_status": status_display,
                "requires_approval": requires_approval
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='check-out', permission_classes=[IsAdminUser])
    def check_out(self, request):
        """
        Employee check-out endpoint (Admin/HR only)
        POST /api/attendance/check-out/
        Body: {"date": "2025-12-01", "location": "OFFICE", "notes": "Optional notes"}
        """
        user = request.user
        
        # Check if user has employee profile
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile to check out."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = user.employee_profile
        serializer = CheckOutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "error": 1,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get date and location
        check_date = serializer.validated_data.get('date', timezone.now().date())
        location = serializer.validated_data.get('location')
        notes = serializer.validated_data.get('notes', '')
        current_time = timezone.now()
        
        with transaction.atomic():
            attendance = Attendance.objects.select_for_update().filter(
                employee=employee,
                date=check_date
            ).first()
            
            if not attendance:
                return Response({
                    "error": 1,
                    "message": f"No check-in found for {check_date}. Please check in first."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate location-specific check-out
            if location == 'OFFICE':
                if not attendance.office_in_time:
                    return Response({
                        "error": 1,
                        "message": f"No office check-in found for {check_date}. Please check in at office first."
                    }, status=status.HTTP_400_BAD_REQUEST)
                if attendance.office_out_time:
                    return Response({
                        "error": 1,
                        "message": f"Already checked out from office for {check_date}"
                    }, status=status.HTTP_400_BAD_REQUEST)
                attendance.office_out_time = current_time
                
            elif location == 'HOME':
                if not attendance.home_in_time:
                    return Response({
                        "error": 1,
                        "message": f"No home check-in found for {check_date}. Please check in at home first."
                    }, status=status.HTTP_400_BAD_REQUEST)
                if attendance.home_out_time:
                    return Response({
                        "error": 1,
                        "message": f"Already checked out from home for {check_date}"
                    }, status=status.HTTP_400_BAD_REQUEST)
                attendance.home_out_time = current_time
            
            if notes:
                attendance.text = notes
            attendance.updated_by = user
            
            # Save will trigger time calculations
            self._determine_day_type(attendance)
            attendance.save()
        
        # Format response
        from .serializers import format_seconds_to_time, format_time_to_12hr
        
        location_in_time = attendance.office_in_time if location == 'OFFICE' else attendance.home_in_time
        location_out_time = attendance.office_out_time if location == 'OFFICE' else attendance.home_out_time
        location_seconds = attendance.office_seconds_worked if location == 'OFFICE' else attendance.home_seconds_worked
        
        return Response({
            "error": 0,
            "data": {
                "message": f"Checked out successfully from {location.lower()}",
                "attendance_id": attendance.id,
                "location": location,
                "check_in_time": format_time_to_12hr(location_in_time),
                "check_out_time": format_time_to_12hr(location_out_time),
                f"{location.lower()}_time": format_seconds_to_time(location_seconds),
                "total_time": format_seconds_to_time(attendance.seconds_actual_worked_time),
                "office_time": format_seconds_to_time(attendance.office_seconds_worked),
                "home_time": format_seconds_to_time(attendance.home_seconds_worked),
                "extra_time": format_seconds_to_time(attendance.seconds_extra_time),
                "extra_time_status": attendance.extra_time_status,
                "date": attendance.date.strftime(DATE_FORMAT)
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='monthly')
    def monthly_attendance(self, request):
        """
        Get monthly attendance summary
        GET /api/attendance/monthly/?month=12&year=2025&userid=838
        Returns: {error: 0, data: {...}} matching your API format
        """
        user = request.user
        
        # Get query parameters
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        userid = request.query_params.get('userid')
        
        # Validate month and year
        if not month or not year:
            return Response({
                "error": 1,
                "message": "month and year query parameters are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            month = int(month)
            year = int(year)
            
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")
        except ValueError as e:
            return Response({
                "error": 1,
                "message": f"Invalid month or year: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get employee
        if userid:
            # Admin can view any employee's attendance
            if user.is_staff:
                try:
                    employee = Employee.objects.get(id=int(userid))
                except (Employee.DoesNotExist, ValueError):
                    return Response({
                        "error": 1,
                        "message": "Employee not found"
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Regular users can only view their own
                if not hasattr(user, 'employee_profile') or str(user.employee_profile.id) != str(userid):
                    return Response({
                        "error": 1,
                        "message": "You can only view your own attendance"
                    }, status=status.HTTP_403_FORBIDDEN)
                employee = user.employee_profile
        else:
            # Default to logged-in user's employee profile
            if not hasattr(user, 'employee_profile'):
                return Response({
                    "error": 1,
                    "message": "User must have an employee profile"
                }, status=status.HTTP_400_BAD_REQUEST)
            employee = user.employee_profile
        
        # Get attendance records for the month
        start_date = datetime(year, month, 1).date()
        num_days = monthrange(year, month)[1]
        end_date = datetime(year, month, num_days).date()
        
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Get holidays for the month
        holidays_list = Holiday.objects.filter(
            date__year=year,
            date__month=month,
            is_active=True
        )
        
        # Get leaves for the month
        from leaves.models import Leave
        leaves_list = Leave.objects.filter(
            employee=employee,
            from_date__lte=end_date,
            to_date__gte=start_date
        ).order_by('from_date')
        
        # Serialize monthly data
        response_data = MonthlyAttendanceSerializer.serialize_monthly_data(
            attendance_records,
            employee,
            month,
            year,
            holidays_list,
            leaves_list
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        """
        Get today's attendance for logged-in employee
        GET /api/attendance/today/
        """
        user = request.user
        
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = user.employee_profile
        today = timezone.now().date()
        
        attendance = Attendance.objects.filter(
            employee=employee,
            date=today
        ).first()
        
        if not attendance:
            return Response({
                "error": 0,
                "data": {
                    "message": "No attendance record for today",
                    "date": today.strftime(DATE_FORMAT),
                    "has_check_in": False,
                    "has_check_out": False
                }
            })
        
        serializer = AttendanceDetailSerializer(attendance)
        return Response({
            "error": 0,
            "data": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='my-attendance')
    def my_attendance(self, request):
        """
        Get logged-in employee's attendance history
        GET /api/attendance/my-attendance/?start_date=2025-12-01&end_date=2025-12-31
        """
        user = request.user
        
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = user.employee_profile
        queryset = Attendance.objects.filter(employee=employee)
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, DATE_FORMAT).date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                return Response({
                    "error": 1,
                    "message": f"Invalid start_date format. Use {DATE_FORMAT}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, DATE_FORMAT).date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                return Response({
                    "error": 1,
                    "message": f"Invalid end_date format. Use {DATE_FORMAT}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AttendanceDetailSerializer(page, many=True)
            return self.get_paginated_response({
                "error": 0,
                "data": serializer.data
            })
        
        serializer = AttendanceDetailSerializer(queryset, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Get weekly timesheet for an employee.",
        manual_parameters=[
            openapi.Parameter('week_start', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Start date of the week (YYYY-MM-DD)"),
            openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Optional: ID of the employee (Admins only)"),
            openapi.Parameter('userid', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Legacy: ID of the employee (Admins only)"),
        ],
        responses={200: WeeklyTimesheetSerializer()}
    )
    @action(detail=False, methods=['get'], url_path='weekly')
    def weekly_timesheet(self, request):
        """
        Get weekly timesheet data
        GET /api/attendance/weekly/?week_start=2025-12-22&user_id=838
        Returns 7 days (Monday to Sunday) with attendance data
        """
        user = request.user
        
        # Get query parameters
        week_start = request.query_params.get('week_start')
        userid = request.query_params.get('user_id') or request.query_params.get('userid')
        
        # Validate week_start
        if not week_start:
            return Response({
                "error": 1,
                "message": "week_start query parameter is required (YYYY-MM-DD format)"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            week_start_date = datetime.strptime(week_start, DATE_FORMAT).date()
        except ValueError:
            return Response({
                "error": 1,
                "message": f"Invalid week_start format. Use {DATE_FORMAT}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure week_start is Monday (adjust if needed)
        days_since_monday = week_start_date.weekday()
        if days_since_monday != 0:
            week_start_date = week_start_date - timedelta(days=days_since_monday)
        
        # Get employee
        if userid:
            # Admin can view any employee's attendance
            if user.is_staff:
                try:
                    employee = Employee.objects.get(id=int(userid))
                except (Employee.DoesNotExist, ValueError):
                    return Response({
                        "error": 1,
                        "message": "Employee not found"
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Regular users can only view their own
                if not hasattr(user, 'employee_profile') or str(user.employee_profile.id) != str(userid):
                    return Response({
                        "error": 1,
                        "message": "You can only view your own attendance"
                    }, status=status.HTTP_403_FORBIDDEN)
                employee = user.employee_profile
        else:
            # Default to logged-in user's employee profile
            if not hasattr(user, 'employee_profile'):
                return Response({
                    "error": 1,
                    "message": "User must have an employee profile"
                }, status=status.HTTP_400_BAD_REQUEST)
            employee = user.employee_profile
        
        # Calculate week range (Monday to Sunday)
        week_end_date = week_start_date + timedelta(days=6)
        
        # Get attendance records for the week
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__gte=week_start_date,
            date__lte=week_end_date
        ).order_by('date')
        
        # Serialize weekly data
        response_data = WeeklyTimesheetSerializer.serialize_weekly_data(
            attendance_records,
            employee,
            week_start_date
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='submit-timesheet')
    def submit_weekly_timesheet(self, request):
        """
        Submit timesheet entry for a specific day
        POST /api/attendance/submit-timesheet/
        Body (multipart/form-data): {
            "date": "2025-12-24",
            "total_time": "8",
            "comments": "Work description...",
            "tracker_screenshot": <file>,
            "is_working_from_home": true,
            "home_in_time": "10:30 AM",  // optional
            "home_out_time": "06:30 PM"  // optional
        }
        """
        user = request.user
        
        # Check if user has employee profile
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile to submit timesheet."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = user.employee_profile
        
        # Create serializer with employee context
        serializer = WeeklyTimesheetSubmitSerializer(
            data=request.data,
            context={'employee': employee, 'request': request}
        )
        
        if not serializer.is_valid():
            return Response({
                "error": 1,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get validated data
        date = serializer.validated_data['date']
        total_time_str = serializer.validated_data['total_time']
        comments = serializer.validated_data.get('comments', '').strip()
        tracker_screenshot = serializer.validated_data.get('tracker_screenshot')
        is_working_from_home = serializer.validated_data.get('is_working_from_home', False)
        home_in_time_str = serializer.validated_data.get('home_in_time', '').strip()
        home_out_time_str = serializer.validated_data.get('home_out_time', '').strip()
        
        # Parse total_time to seconds
        try:
            total_time_float = float(total_time_str)
            total_time_seconds = int(total_time_float * 3600)
        except ValueError:
            return Response({
                "error": 1,
                "message": f"Invalid total_time format: {total_time_str}. Use format like '8' or '8.5'"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Check for existing attendance record
            existing = Attendance.objects.select_for_update().filter(
                employee=employee,
                date=date
            ).first()
            
            # Handle resubmission (only if REJECTED)
            if existing:
                if hasattr(existing, 'timesheet_status') and existing.timesheet_status in ['PENDING', 'APPROVED']:
                    status_display = existing.get_timesheet_status_display() if hasattr(existing, 'get_timesheet_status_display') else existing.timesheet_status
                    return Response({
                        "error": 1,
                        "message": f"Timesheet already submitted for this date. Status: {status_display}"
                    }, status=status.HTTP_400_BAD_REQUEST)
                # If REJECTED, allow update/resubmission
                attendance = existing
            else:
                # Create new attendance record
                attendance = Attendance.objects.create(
                    employee=employee,
                    date=date,
                    office_working_hours=getattr(settings, 'ATTENDANCE_DEFAULT_WORKING_HOURS', '09:00'),
                    orignal_total_time=getattr(settings, 'ATTENDANCE_DEFAULT_TOTAL_TIME_SECONDS', 32400),
                    created_by=user,
                    updated_by=user
                )
            
            # Handle tracker screenshot (Cloudinary public ID/path)
            if tracker_screenshot and hasattr(attendance, 'tracker_screenshot'):
                attendance.tracker_screenshot = tracker_screenshot
            
            # Set home times
            home_in_time = None
            home_out_time = None
            
            if is_working_from_home:
                # If user provided times, parse them
                if home_in_time_str:
                    try:
                        home_in_time = serializer.parse_time_string(home_in_time_str, date)
                    except Exception as e:
                        return Response({
                            "error": 1,
                            "message": str(e)
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                if home_out_time_str:
                    try:
                        home_out_time = serializer.parse_time_string(home_out_time_str, date)
                    except Exception as e:
                        return Response({
                            "error": 1,
                            "message": str(e)
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # If times not provided, auto-calculate based on office hours
                if not home_in_time or not home_out_time:
                    # Get office start time (default 9 AM)
                    office_hours = attendance.office_working_hours or '09:00'
                    hour, minute = map(int, office_hours.split(':'))
                    
                    # Set start time
                    if not home_in_time:
                        home_in_time = timezone.make_aware(
                            datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                        )
                    
                    # Calculate end time based on total_time
                    if not home_out_time:
                        home_out_time = home_in_time + timedelta(seconds=total_time_seconds)
            
            # Update attendance record
            attendance.is_working_from_home = is_working_from_home
            attendance.home_in_time = home_in_time
            attendance.home_out_time = home_out_time
            attendance.text = comments
            attendance.day_text = comments
            attendance.seconds_actual_worked_time = total_time_seconds
            attendance.timesheet_submitted_at = timezone.now()
            
            # Set status: auto-approve non-WFH, PENDING for WFH
            if is_working_from_home:
                attendance.timesheet_status = 'PENDING'
            else:
                attendance.timesheet_status = 'APPROVED'
                attendance.timesheet_approved_by = user
                attendance.timesheet_approved_at = timezone.now()
            
            attendance.updated_by = user
            attendance.entry_type = 'TIMESHEET'
            self._determine_day_type(attendance)
            
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                attendance.save()
            except DjangoValidationError as e:
                return Response({
                    "error": 1,
                    "message": "Validation failed: " + str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    "error": 1,
                    "message": "An error occurred: " + str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Format response
        status_display = attendance.get_timesheet_status_display()
        
        # Determine if approval is required
        requires_approval = is_working_from_home and not (user.is_staff or user.is_superuser)
        
        return Response({
            "error": 0,
            "data": {
                "message": "Timesheet submitted successfully" + (". Pending admin approval." if requires_approval else ""),
                "attendance_id": attendance.id,
                "status": status_display,
                "date": attendance.date.strftime(DATE_FORMAT),
                "is_working_from_home": attendance.is_working_from_home,
                "auto_approved": not is_working_from_home,
                "requires_approval": requires_approval
            }
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Manually create or update attendance for a specific day.",
        request_body=UpdateSessionSerializer,
        responses={200: "Success Response"}
    )
    @action(detail=False, methods=['post'], url_path='manual-update')
    def manual_update(self, request):
        """
        Manually create or update attendance for a specific day.
        POST /api/attendance/manual-update/
        """
        user = request.user
        
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = user.employee_profile
        serializer = UpdateSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "error": 1,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract data
        date = serializer.validated_data['date']
        in_time_str = serializer.validated_data['in_time']
        out_time_str = serializer.validated_data['out_time']
        is_working_from_home = serializer.validated_data.get('is_working_from_home', False)
        
        # Parse times
        try:
            in_time = serializer.parse_time_string(in_time_str, date)
            out_time = serializer.parse_time_string(out_time_str, date)
        except Exception as e:
            return Response({
                "error": 1,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if out_time < in_time:
            return Response({
                "error": 1,
                "message": "Out time cannot be before in time"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate worked seconds
        worked_seconds = int((out_time - in_time).total_seconds())
        
        with transaction.atomic():
            # Create or update attendance record
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=date,
                defaults={
                    'office_working_hours': getattr(settings, 'ATTENDANCE_DEFAULT_WORKING_HOURS', '09:00'),
                    'orignal_total_time': getattr(settings, 'ATTENDANCE_DEFAULT_TOTAL_TIME_SECONDS', 32400),
                    'created_by': user,
                    'updated_by': user
                }
            )
            
            # Update times
            if is_working_from_home:
                attendance.home_in_time = in_time
                attendance.home_out_time = out_time
                attendance.is_working_from_home = True
            else:
                attendance.office_in_time = in_time
                attendance.office_out_time = out_time
                attendance.is_working_from_home = False
            
            # Update general fields
            attendance.in_time = in_time
            attendance.out_time = out_time
            attendance.seconds_actual_worked_time = worked_seconds
            attendance.updated_by = user
            
            # Auto-approve manual updates if they are not WFH or if submitted by admin
            if hasattr(attendance, 'timesheet_status'):
                if is_working_from_home and not user.is_staff:
                    attendance.timesheet_status = 'PENDING'
                else:
                    attendance.timesheet_status = 'APPROVED'
                    if hasattr(attendance, 'timesheet_approved_by'):
                        attendance.timesheet_approved_by = user
                    if hasattr(attendance, 'timesheet_approved_at'):
                        attendance.timesheet_approved_at = timezone.now()
            attendance.entry_type = 'MANUAL'
            self._determine_day_type(attendance)
            attendance.save()
        
        # Calculate progress for response
        total_goal = attendance.orignal_total_time or 32400
        progress = (worked_seconds / total_goal) * 100
        goal_status = "Goal Reached" if worked_seconds >= total_goal else "Goal Pending"
        
        return Response({
            "error": 0,
            "message": "Attendance updated successfully",
            "data": {
                "id": attendance.id,
                "full_date": attendance.date.strftime("%Y-%m-%d"),
                "total_time": format_seconds_to_hms(worked_seconds),
                "goal_status": goal_status,
                "progress_percentage": min(round(progress, 2), 100.0),
                "in_time": format_datetime_to_iso(in_time),
                "out_time": format_datetime_to_iso(out_time),
                "day_type": attendance.day_type,
                "is_working_from_home": attendance.is_working_from_home
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post', 'patch'], url_path='approve', permission_classes=[IsAdminUser])
    def approve_timesheet(self, request, pk=None):
        """
        Admin approval/rejection endpoint
        POST /api/attendance/{id}/approve/
        Body: {
            "action": "approve",  // or "reject"
            "admin_notes": "Optional notes"
        }
        """
        user = request.user
        
        # Check if user is admin/staff
        if not user.is_staff:
            return Response({
                "error": 1,
                "message": "Only admin/staff users can approve/reject timesheets"
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            attendance = Attendance.objects.get(pk=pk)
        except Attendance.DoesNotExist:
            return Response({
                "error": 1,
                "message": "Attendance record not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate action
        action = request.data.get('action', '').lower()
        if action not in ['approve', 'reject']:
            return Response({
                "error": 1,
                "message": "Invalid action. Use 'approve' or 'reject'"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if record is pending (only if timesheet_status field exists)
        if hasattr(attendance, 'timesheet_status'):
            if attendance.timesheet_status != 'PENDING':
                status_display = attendance.get_timesheet_status_display() if hasattr(attendance, 'get_timesheet_status_display') else attendance.timesheet_status
                return Response({
                    "error": 1,
                    "message": f"Can only approve/reject PENDING timesheets. Current status: {status_display}"
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "error": 1,
                "message": "Timesheet status feature is not available in this model"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_notes = request.data.get('admin_notes', '').strip()
        
        # Require admin_notes for rejection
        if action == 'reject' and not admin_notes:
            return Response({
                "error": 1,
                "message": "Admin notes are required when rejecting a timesheet"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update attendance record (only if timesheet fields exist)
        if hasattr(attendance, 'timesheet_status'):
            attendance.timesheet_status = 'APPROVED' if action == 'approve' else 'REJECTED'
        if hasattr(attendance, 'timesheet_approved_by'):
            attendance.timesheet_approved_by = user
        if hasattr(attendance, 'timesheet_approved_at'):
            attendance.timesheet_approved_at = timezone.now()
        if hasattr(attendance, 'timesheet_admin_notes'):
            attendance.timesheet_admin_notes = admin_notes
        attendance.updated_by = user
        attendance.save()
        
        # Get status display safely
        status_display = ""
        if hasattr(attendance, 'get_timesheet_status_display'):
            try:
                status_display = attendance.get_timesheet_status_display()
            except (AttributeError, ValueError):
                status_display = getattr(attendance, 'timesheet_status', '')
        
        # Get approved_at safely
        approved_at = None
        if hasattr(attendance, 'timesheet_approved_at'):
            approved_at = format_datetime_to_iso(attendance.timesheet_approved_at)
        
        return Response({
            "error": 0,
            "data": {
                "message": f"Timesheet {action}d successfully",
                "attendance_id": attendance.id,
                "status": status_display,
                "approved_by": user.email,
                "approved_at": approved_at,
                "admin_notes": admin_notes if action == 'reject' else None
            }
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to allow deletion of REJECTED timesheets only
        DELETE /api/attendance/{id}/
        """
        instance = self.get_object()
        user = request.user
        
        # Check permissions
        if not user.is_staff:
            # Regular users can only delete their own records
            if not hasattr(user, 'employee_profile') or instance.employee != user.employee_profile:
                return Response({
                    "error": 1,
                    "message": "You can only delete your own attendance records"
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if record can be deleted (only REJECTED)
        if hasattr(instance, 'timesheet_status') and instance.timesheet_status != 'REJECTED':
            return Response({
                "error": 1,
                "message": f"Can only delete REJECTED timesheets. Current status: {instance.get_timesheet_status_display()}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the record
        self.perform_destroy(instance)
        
        return Response({
            "error": 0,
            "data": {
                "message": "Rejected timesheet deleted successfully. You can now resubmit for this date."
            }
        }, status=status.HTTP_200_OK)

