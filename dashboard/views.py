from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Q
from employees.models import Employee
from attendance.models import Attendance
from leaves.models import LeaveBalance, RestrictedHoliday
from holidays.models import Holiday
import logging

logger = logging.getLogger(__name__)

class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if not hasattr(user, 'employee_profile'):
                return Response({
                    "error": 1,
                    "message": "Employee profile not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            employee = user.employee_profile
            today = timezone.now().date()
            current_month = today.month
            current_year = today.year
            
            # 1. User Info
            data = {
                "user": {
                    "first_name": employee.first_name,
                    "full_name": employee.full_name,
                    "date": today.strftime("%B %d, %Y")
                }
            }
            
            # 2. Monthly Attendance Summary
            month_start = today.replace(day=1)
            
            # Present Days
            monthly_attendances = Attendance.objects.filter(
                employee=employee,
                date__month=current_month,
                date__year=current_year
            )
            
            present_days = monthly_attendances.filter(day_type='WORKING_DAY').count()
            half_days = monthly_attendances.filter(day_type='HALF_DAY').count()
            effective_present = present_days + (half_days * 0.5)
            
            # Calculate business days passed
            business_days_till_today = 0
            holidays_in_month = Holiday.objects.filter(
                date__month=current_month, 
                date__year=current_year, 
                is_active=True
            ).values_list('date', flat=True)
            
            current_date_it = month_start
            while current_date_it <= today:
                if current_date_it.weekday() < 5 and current_date_it not in holidays_in_month:
                    business_days_till_today += 1
                current_date_it += timedelta(days=1)
                
            attendance_percentage = (effective_present / business_days_till_today * 100) if business_days_till_today > 0 else 0
            
            # 3. Leave Balance Summary
            balances = LeaveBalance.objects.filter(employee=employee, year=current_year)
            total_remaining = sum([float(b.available) for b in balances])
            
            # Add RH available
            casual_balance = balances.filter(leave_type='Casual Leave').first()
            if casual_balance:
                total_remaining += float(casual_balance.rh_available)

            data["overview"] = {
                "monthly_attendance_pct": f"{int(attendance_percentage)}%",
                "attendance_trend": "+2.4%",
                "leave_balance": f"{int(total_remaining)} Days",
                "tasks_completed": 28,
                "tasks_trend": "+5%",
                "employee_score": 4.8
            }

            # 4. Productivity Last 7 Days
            last_7_days_graph = []
            seven_days_ago = today - timedelta(days=6)
            
            total_worked_seconds = 0
            days_counted = 0
            
            current_date_it = seven_days_ago
            while current_date_it <= today:
                # Use cached monthly_attendances if possible or fetch specifically
                day_att = Attendance.objects.filter(employee=employee, date=current_date_it).first()
                worked_seconds = day_att.seconds_actual_worked_time if day_att else 0
                worked_hours = round(worked_seconds / 3600.0, 1)
                
                last_7_days_graph.append({
                    "date": current_date_it.strftime("%b %d"),
                    "hours": worked_hours
                })
                
                if worked_hours > 0:
                    total_worked_seconds += worked_seconds
                    days_counted += 1
                
                current_date_it += timedelta(days=1)
                
            avg_hours = round((total_worked_seconds / 3600.0 / days_counted), 1) if days_counted > 0 else 0
            
            data["productivity"] = {
                "daily_average": f"{avg_hours}h",
                "graph_data": last_7_days_graph
            }

            # 5. Detailed Leave Balance (Breakdown)
            leave_breakdown = []
            for b in balances:
                leave_breakdown.append({
                    "label": b.leave_type,
                    "value": float(b.available)
                })
            
            if casual_balance:
                 leave_breakdown.append({
                    "label": "Restricted Holiday",
                    "value": float(casual_balance.rh_available)
                })

            data["leave_chart"] = {
                "total_left": int(total_remaining),
                "breakdown": leave_breakdown
            }

            # 6. Upcoming Holidays
            upcoming_h = Holiday.objects.filter(date__gte=today, is_active=True).order_by('date')[:3]
            data["upcoming_holidays"] = [
                {
                    "name": h.name,
                    "type": "Company-wide Holiday",
                    "date": h.date.strftime("%b %d")
                } for h in upcoming_h
            ]

            # 7. Performance Card
            data["performance_widget"] = {
                "title": "Top Performer!",
                "message": f"Great job, {employee.first_name}! Your efficiency this week is 15% higher than the team average.",
                "efficiency_gain": "15%"
            }

            return Response({"error": 0, "data": data})

        except Exception as e:
            logger.error(f"Dashboard Error: {str(e)}")
            return Response({
                "error": 1,
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
