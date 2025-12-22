from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SalaryStructure, Payslip, PayrollConfig
from .serializers import SalaryStructureSerializer, PayslipSerializer, SalaryOverviewSerializer, PayrollConfigSerializer
from .services import PayrollService
from employees.models import Employee
from django.shortcuts import get_object_or_404
from django.utils import timezone

class UserSalaryInfoView(APIView):
    """
    Returns salary info for the logged-in user.
    Synchronizes with leaves and holidays (logic to be expanded in detailed calculation service).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_object_or_404(Employee, user=request.user)
        
        # Get salary structure (plural if historical, but here we take current)
        salary_structure = SalaryStructure.objects.filter(employee=employee, is_active=True)
        
        # Get payslip history
        payslips = Payslip.objects.filter(employee=employee).order_by('-year', '-month')
        
        # Get current month preview
        now = timezone.now()
        salary_preview = PayrollService.calculate_monthly_salary(employee, now.month, now.year)
        
        data = {
            "id": str(request.user.id),
            "name": employee.get_full_name(),
            "email": employee.email,
            "date_of_joining": employee.joining_date,
            "type": "employee",
            "current_month_preview": salary_preview,
            "salary_details": SalaryStructureSerializer(salary_structure, many=True).data,
            "payslip_history": PayslipSerializer(payslips, many=True).data,
            "holding_details": []
        }
        
        return Response({
            "error": 0,
            "data": data
        })

class GenericConfigurationView(APIView):
    """
    Returns generic HR/Payroll configurations.
    """
    # Some configs might be public or authenticated
    permission_classes = [IsAuthenticated]

    def get(self, request):
        configs = PayrollConfig.objects.all()
        config_data = {c.key: c.value for c in configs}
        
        # Default fallbacks if not in DB to match prototype
        defaults = {
            "login_types": {
                "normal_login": True,
                "google_login": False
            },
            "attendance_late_days": 4,
            "web_show_salary": 1,
            "rh_config": {
                "rh_per_quater": 1,
                "rh_extra": 1,
                "rh_rejection_setting": False
            }
        }
        
        merged_data = {**defaults, **config_data}
        
        return Response({
            "error": False,
            "data": merged_data
        })
