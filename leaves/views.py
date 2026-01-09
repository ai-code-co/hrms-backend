from django.shortcuts import render
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import timedelta, date
from .models import Leave, LeaveBalance, LeaveQuota, RestrictedHoliday
from holidays.models import Holiday
from .serializers import (
    LeaveSerializer, LeaveCalculationSerializer, LeaveBalanceSerializer,
    LeaveQuotaSerializer, RestrictedHolidaySerializer
)
from django.db.models import Q, Sum
import logging

logger = logging.getLogger(__name__)

class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Admins see all leaves.
        Regular users see only their own leaves.
        """
        user = self.request.user
        
        # Admins can see all leaves
        if user.is_staff:
            return Leave.objects.all()
        
        # Check if user has employee profile
        if not hasattr(user, 'employee_profile'):
            return Leave.objects.none()  # Return empty queryset
        
        # Regular users see only their own leaves
        return Leave.objects.filter(employee=user.employee_profile)

    @swagger_auto_schema(
        operation_description="Gateway endpoint to handle different actions (e.g., apply_leave, get_days_between_leaves).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['apply_leave', 'get_days_between_leaves'],
                    description="Action to perform"
                ),
            },
            required=['action']
        ),
        responses={200: openapi.Response("Successful Dispatch")}
    )
    def create(self, request, *args, **kwargs):
        """
        Gateway method to handle different actions if sent to the main POST endpoint.
        """
        action_type = request.data.get('action')
        
        if action_type == 'get_days_between_leaves':
            return self.calculate_days(request)
        elif action_type == 'apply_leave':
            return self.submit_leave(request)
        # Add more action handlers here if needed
        
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # OLD CODE: serializer.save(employee=self.request.user)
        # NEW CODE (2025-12-22): Save with Employee
        user = self.request.user
        if not hasattr(user, 'employee_profile'):
            raise serializers.ValidationError("User must have an employee profile")
        serializer.save(employee=user.employee_profile)

    @swagger_auto_schema(
        operation_description="Calculate working days, weekends, and holidays between two dates.",
        request_body=LeaveCalculationSerializer,
        responses={200: openapi.Response("Success", openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "error": openapi.Schema(type=openapi.TYPE_INTEGER),
                "data": openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ))}
    )
    @action(detail=False, methods=['post'], url_path='calculate-days')
    def calculate_days(self, request):
        """
        API to calculate working days, weekends, and holidays between two dates.
        Expected Payload: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
        User Prototype Payload used 'action': 'get_days_between_leaves', but we use a REST path.
        """
        
        # Determine start/end date from request data (handle both direct keys and 'action' style if needed)
        start_date_str = request.data.get('start_date') or request.data.get('from_date')
        end_date_str = request.data.get('end_date') or request.data.get('to_date')

        if not start_date_str or not end_date_str:
             return Response({"error": 1, "message": "start_date and end_date are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)

        if not start_date or not end_date:
            return Response({"error": 1, "message": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        # Logic to calculate days
        current_date = start_date
        working_days = 0
        holidays_count = 0
        weekends = 0
        days_details = []

        # Fetch holidays in range
        holidays_in_range = Holiday.objects.filter(
            date__range=[start_date, end_date], 
            is_active=True
        ).values_list('date', flat=True)

        while current_date <= end_date:
            day_type = "working"
            sub_type = ""
            
            # Check for Weekend (Sat=5, Sun=6)
            if current_date.weekday() in [5, 6]:
                weekends += 1
                day_type = "weekend"
                sub_type = "Saturday" if current_date.weekday() == 5 else "Sunday"
            
            # Check for Holiday (overrides weekend if we want strict accounting, or counts as both? 
            # Usually strict accounting means 1 day is either Holiday OR Weekend OR Working. 
            # Let's assume Holiday takes precedence or is counted separately. 
            # The user output shows 'holidays': 0, 'weekends': 0. 
            # Let's count them mutually exclusively for the total 'working_days' calculation.)

            is_holiday = current_date in holidays_in_range
            
            if is_holiday:
                holidays_count += 1
                day_type = "holiday"
                # If it was also a weekend, we might not want to double count the 'non-working' aspect, 
                # but valid metrics usually count "Weekends" and "Holidays" separately. 
                # However, for 'working_days', both reduce the count.
                if current_date.weekday() in [5, 6]:
                     # It's a weekend AND a holiday. 
                     # Should we decrement weekend count? Depends on business logic.
                     # Let's keep specific counters correct: It IS a weekend, and it IS a holiday.
                     pass

            if day_type == "working":
                working_days += 1

            days_details.append({
                "type": day_type,
                "sub_type": sub_type,
                "sub_sub_type": "", # Placeholder as per prototype
                "full_date": current_date.strftime("%Y-%m-%d")
            })

            current_date += timedelta(days=1)

        response_data = {
            "error": 0,
            "data": {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "working_days": working_days,
                "holidays": holidays_count,
                "weekends": weekends,
                "days": days_details,
                "message": ""
            }
        }
        return Response(response_data)


    @swagger_auto_schema(
        operation_description="Submit a new leave request (Alternative REST endpoint).",
        request_body=LeaveSerializer,
        responses={201: openapi.Response("Leave applied successfully")}
    )
    @action(detail=False, methods=['post'], url_path='submit-leave')
    def submit_leave(self, request):
        """
        Custom endpoint to match user's 'apply_leave' payload structure.
        """
        user = request.user
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1, 
                "message": "User must have an employee profile to apply for leaves."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check for manual attendance entries before allowing leave application
            from attendance.models import Attendance
            from_date = serializer.validated_data.get('from_date')
            to_date = serializer.validated_data.get('to_date')
            
            # Check if any manual attendance entries exist in the date range
            manual_entries = Attendance.objects.filter(
                employee=user.employee_profile,
                date__gte=from_date,
                date__lte=to_date,
                entry_type__in=['MANUAL', 'TIMESHEET']
            ).order_by('date')
            
            if manual_entries.exists():
                # Get the first conflicting date for error message
                first_conflict = manual_entries.first()
                entry_type_display = first_conflict.get_entry_type_display() if hasattr(first_conflict, 'get_entry_type_display') else first_conflict.entry_type
                
                return Response({
                    "error": 1,
                    "message": f"Cannot apply leave. You have already submitted {entry_type_display} attendance for {first_conflict.date.strftime('%Y-%m-%d')}. Please remove the manual entry first."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # The serializer's validate() already checks balances.
                # The serializer's create() handles linking the restricted_holiday if 'rh_id' is passed.
                leave = serializer.save(employee=user.employee_profile)

                # Balance updates (adding to pending) are handled by update_balance_on_leave_create signal.
                
                return Response({
                    "error": 0, 
                    "data": {
                        "message": "Leave applied successfully.",
                        "leave_id": leave.id,
                        "status": leave.status,
                        "is_restricted": leave.leave_type == Leave.LeaveType.RESTRICTED_HOLIDAY
                    }
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Error applying leave: {str(e)}")
                return Response({"error": 1, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "error": 1,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='upload-doc')
    def upload_doc(self, request):
        """
        Uploads a file. 
        Expects 'file' in FILES and 'document_type' in DATA.
        """
        uploaded_file = request.FILES.get('file')
        # user sends document_type='leave_doc'
        
        if not uploaded_file:
             return Response({"error": 1, "message": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # If the user wants a standalone upload endpoint that just saves the file and returns success:
        return Response({"error": 0, "message": "Uploaded successfully!!"})

    @action(detail=False, methods=['get'], url_path='rh-balance')
    def get_rh_balance(self, request):
        """
        Endpoint to get the remaining Restricted Holiday balance AND 
        the list of active Restricted Holidays for the year.
        """
        user = request.user
        if not hasattr(user, 'employee_profile'):
            return Response({"error": 1, "message": "Employee profile required."}, status=404)
            
        current_year = timezone.now().year
        # 1. Get RH Balance (tracked on Casual Leave record)
        balance = LeaveBalance.objects.filter(
            employee=user.employee_profile,
            leave_type='Casual Leave',
            year=current_year
        ).first()
        
        if not balance:
            return Response({"error": 1, "message": "No leaf balance found."}, status=404)
            
        # 2. Get list of active Restricted Holidays for the year
        rh_list = RestrictedHoliday.objects.filter(
            is_active=True,
            date__year=current_year
        )
        
        # 3. Exclude holidays already applied for (Pending or Approved)
        applied_rh_ids = Leave.objects.filter(
            employee=user.employee_profile,
            leave_type='Restricted Holiday',
            status__in=['Pending', 'Approved'],
            restricted_holiday__isnull=False
        ).values_list('restricted_holiday_id', flat=True)
        
        rh_list = rh_list.exclude(id__in=applied_rh_ids)
        
        rh_serializer = RestrictedHolidaySerializer(rh_list, many=True)
            
        # 4. If no balance left, return empty list
        if balance.rh_available <= 0:
            rh_serializer_data = []
        else:
            rh_serializer_data = rh_serializer.data
            
        return Response({
            "error": 0,
            "data": {
                "balance": {
                    "rh_allocated": balance.rh_allocated,
                    "rh_used": balance.rh_used,
                    "rh_available": balance.rh_available
                },
                "holidays": rh_serializer_data
            }
        })

    @swagger_auto_schema(
        operation_description="Get leave balance for the logged-in user.",
        responses={200: LeaveBalanceSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='balance')
    def get_balance(self, request):
        """
        Get leave balance for the logged-in user.
        Returns balance for all leave types.
        """
        # OLD CODE: employee = request.user
        # NEW CODE (2025-12-22): Get Employee from User
        user = request.user
        
        # Check if user has employee profile
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile. Please contact HR."
            }, status=status.HTTP_404_NOT_FOUND)
        
        employee = user.employee_profile
        current_year = timezone.now().year
        
        balances = LeaveBalance.objects.filter(
            employee=employee,
            year=current_year
        )
        
        if not balances.exists():
            return Response({
                "error": 1,
                "message": "No leave balance configured. Please contact HR."
            }, status=status.HTTP_404_NOT_FOUND)
        
        balance_data = {}
        for balance in balances:
            balance_data[balance.leave_type] = {
                "allocated": float(balance.total_allocated),
                "used": float(balance.used),
                "pending": float(balance.pending),
                "available": float(balance.available),
                "carried_forward": float(balance.carried_forward)
            }

            if balance.leave_type == 'Restricted Holiday':
                 balance_data[balance.leave_type]['rh_details'] = {
                     "allocated": balance.rh_allocated,
                     "used": balance.rh_used,
                     "available": balance.rh_available
                 }
        
        # Add RH balance (assuming one RH balance per employee)
        rh_balance = balances.filter(leave_type='Casual Leave').first()
        if rh_balance:
            balance_data['rh'] = {
                "allocated": rh_balance.rh_allocated,
                "used": rh_balance.rh_used,
                "pending": rh_balance.rh_pending,
                "available": rh_balance.rh_available
            }
        
        return Response({
            "error": 0,
            "data": balance_data
        })

    def perform_create(self, serializer):
        """Override to update balance when leave is created"""
        # OLD CODE: leave = serializer.save(employee=self.request.user)
        # NEW CODE (2025-12-22): Save with Employee
        user = self.request.user
        if not hasattr(user, 'employee_profile'):
            raise serializers.ValidationError("User must have an employee profile")
        
        leave = serializer.save(employee=user.employee_profile)
        
        # Update pending balance
        current_year = timezone.now().year
        try:
            balance = LeaveBalance.objects.get(
                employee=user.employee_profile,  # Changed from self.request.user
                leave_type=leave.leave_type,
                year=current_year
            )
            balance.pending += leave.no_of_days
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass
    
    def perform_update(self, serializer):
        """Save leave updates - balance updates handled by signals"""
        serializer.save()
