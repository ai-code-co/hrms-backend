from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SalaryStructure, Payslip, PayrollConfig
from .serializers import SalaryStructureSerializer, PayslipSerializer, PayslipSummarySerializer, SalaryOverviewSerializer, PayrollConfigSerializer
from .services import PayrollService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from employees.models import Employee
from django.shortcuts import get_object_or_404
from django.utils import timezone

class UserSalaryInfoView(APIView):
    """
    Returns salary info for the logged-in user.
    Synchronizes with leaves and holidays (logic to be expanded in detailed calculation service).
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description=(
            "Get salary and payslip data. "
            "For admin/superuser without userid/employee_id, returns all employees payslips "
            "(optionally filtered by month/year). "
            "With userid/employee_id, returns that employee's salary view."
        ),
        manual_parameters=[
            openapi.Parameter('month', openapi.IN_QUERY, description="Month (1-12)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('year', openapi.IN_QUERY, description="Year (e.g. 2025)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('userid', openapi.IN_QUERY, description="Employee ID (optional)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('employee_id', openapi.IN_QUERY, description="Employee ID (optional alias of userid)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: openapi.Response(
            description="Detailed salary and payslip information",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_STRING),
                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                            "email": openapi.Schema(type=openapi.TYPE_STRING),
                            "annual_ctc": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "bank_details": openapi.Schema(type=openapi.TYPE_OBJECT),
                            "payslip_months": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                            "selected_payslip": openapi.Schema(type=openapi.TYPE_OBJECT),
                        }
                    )
                }
            )
        )}
    )
    def get(self, request):
        user = request.user
        target_id = request.query_params.get('userid') or request.query_params.get('employee_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        month_int = None
        year_int = None

        if (month and not year) or (year and not month):
            return Response(
                {"error": 1, "message": "Both month and year are required together"},
                status=400
            )

        if month and year:
            try:
                month_int = int(month)
                year_int = int(year)
                if month_int < 1 or month_int > 12:
                    raise ValueError("Month must be between 1 and 12")
                if year_int < 1:
                    raise ValueError("Year must be a positive integer")
            except ValueError as exc:
                return Response({"error": 1, "message": str(exc)}, status=400)

        # Specific employee mode
        if target_id:
            can_access = False
            if user.is_staff or user.is_superuser:
                can_access = True
            elif hasattr(user, 'employee_profile'):
                me = user.employee_profile
                if str(me.id) == str(target_id):
                    can_access = True
                elif me.can_view_all_employees():
                    can_access = True
                elif me.can_view_subordinates():
                    target_employee = Employee.objects.filter(
                        id=target_id,
                        reporting_manager_id=me.id
                    ).first()
                    if target_employee:
                        can_access = True

            if not can_access:
                return Response({"error": 1, "message": "Permission denied"}, status=403)

            employee = get_object_or_404(Employee, id=target_id)
            all_payslips = Payslip.objects.filter(employee=employee).order_by('-year', '-month')

            if month_int and year_int:
                selected_payslip = all_payslips.filter(month=month_int, year=year_int).first()
            else:
                selected_payslip = all_payslips.first()

            latest_structure = employee.salary_structures.filter(
                is_active=True
            ).order_by('-applicable_from').first()
            annual_ctc = float(latest_structure.total_earnings * 12) if latest_structure else 0

            data = {
                "id": str(employee.id),
                "name": employee.get_full_name(),
                "email": employee.email,
                "annual_ctc": annual_ctc,
                "bank_details": {
                    "bank_name": employee.bank_name,
                    "account_number": employee.account_number,
                    "ifsc_code": employee.ifsc_code,
                    "masked_account_number": f"**** {employee.account_number[-4:]}" if employee.account_number else ""
                },
                "payslip_months": PayslipSummarySerializer(all_payslips, many=True).data,
                "selected_payslip": PayslipSerializer(selected_payslip).data if selected_payslip else None
            }
            return Response({"error": 0, "data": data})

        # All employees mode (admin/superuser)
        if user.is_staff or user.is_superuser:
            all_payslips = Payslip.objects.all().order_by('-year', '-month', 'employee_id')
            if month_int and year_int:
                all_payslips = all_payslips.filter(month=month_int, year=year_int)

            data = {
                "scope": "all_employees",
                "filters": {
                    "month": month_int,
                    "year": year_int
                },
                "total_payslips": all_payslips.count(),
                "payslips": PayslipSerializer(all_payslips, many=True).data
            }
            return Response({"error": 0, "data": data})

        # Logged-in user's own salary
        employee = get_object_or_404(Employee, user=request.user)
        all_payslips = Payslip.objects.filter(employee=employee).order_by('-year', '-month')
        if month_int and year_int:
            selected_payslip = all_payslips.filter(month=month_int, year=year_int).first()
        else:
            selected_payslip = all_payslips.first()

        latest_structure = employee.salary_structures.filter(is_active=True).order_by('-applicable_from').first()
        annual_ctc = float(latest_structure.total_earnings * 12) if latest_structure else 0

        data = {
            "id": str(employee.id),
            "name": employee.get_full_name(),
            "email": employee.email,
            "annual_ctc": annual_ctc,
            "bank_details": {
                "bank_name": employee.bank_name,
                "account_number": employee.account_number,
                "ifsc_code": employee.ifsc_code,
                "masked_account_number": f"**** {employee.account_number[-4:]}" if employee.account_number else ""
            },
            "payslip_months": PayslipSummarySerializer(all_payslips, many=True).data,
            "selected_payslip": PayslipSerializer(selected_payslip).data if selected_payslip else None
        }

        return Response({"error": 0, "data": data})

class GenericConfigurationView(APIView):
    """
    Returns generic HR/Payroll configurations.
    """
    # Some configs might be public or authenticated
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get general HR and payroll configuration settings.",
        responses={200: openapi.Response(
            description="Configuration key-value pairs",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "login_types": openapi.Schema(type=openapi.TYPE_OBJECT),
                            "attendance_late_days": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "web_show_salary": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "rh_config": openapi.Schema(type=openapi.TYPE_OBJECT),
                        }
                    )
                }
            )
        )}
    )
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
