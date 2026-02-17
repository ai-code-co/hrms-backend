from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SalaryStructure, Payslip, PayrollConfig
from .serializers import (
    SalaryStructureSerializer,
    SalaryStructureAdminUpdateSerializer,
    PayslipSerializer,
    PayslipSummarySerializer,
    SalaryOverviewSerializer,
    PayrollConfigSerializer,
)
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
        payslip_filters = {}

        if month is not None and month != "":
            try:
                month_int = int(month)
            except (TypeError, ValueError):
                return Response({"error": 1, "message": "Month must be an integer between 1 and 12"}, status=400)
            if month_int < 1 or month_int > 12:
                return Response({"error": 1, "message": "Month must be between 1 and 12"}, status=400)
            payslip_filters["month"] = month_int

        if year is not None and year != "":
            try:
                year_int = int(year)
            except (TypeError, ValueError):
                return Response({"error": 1, "message": "Year must be a positive integer"}, status=400)
            if year_int < 1:
                return Response({"error": 1, "message": "Year must be a positive integer"}, status=400)
            payslip_filters["year"] = year_int

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

            if payslip_filters:
                selected_payslip = all_payslips.filter(**payslip_filters).first()
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
            if payslip_filters:
                all_payslips = all_payslips.filter(**payslip_filters)

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
        if payslip_filters:
            selected_payslip = all_payslips.filter(**payslip_filters).first()
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


class SalaryStructureAdminUpdateView(APIView):
    """
    Admin/Superuser can update allowed salary structure fields.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description=(
            "Update salary structure fields for an employee. "
            "Path identifier can be SalaryStructure.id (e.g. 12) or Employee.employee_id (e.g. EMP8413). "
            "Allowed only for admin/superuser."
        ),
        request_body=SalaryStructureAdminUpdateSerializer,
        responses={200: openapi.Response("Salary structure updated successfully")}
    )
    def patch(self, request, identifier):
        user = request.user
        if not (user.is_staff or user.is_superuser):
            return Response(
                {"error": 1, "message": "Only admin/superuser can update salary structure"},
                status=403
            )

        resolved_by = None
        salary_structure = None
        identifier_str = str(identifier).strip()

        # If numeric, first try SalaryStructure primary key.
        if identifier_str.isdigit():
            salary_structure = SalaryStructure.objects.filter(id=int(identifier_str)).first()
            if salary_structure:
                resolved_by = "salary_structure_id"

        # Fallback/alternate: treat identifier as Employee.employee_id (e.g. EMP8413).
        if not salary_structure:
            salary_structure = SalaryStructure.objects.filter(
                employee__employee_id=identifier_str
            ).order_by('-is_active', '-applicable_from', '-updated_at', '-id').first()
            if salary_structure:
                resolved_by = "employee_id"

        if not salary_structure:
            return Response(
                {"error": 1, "message": "Salary structure not found for the provided identifier"},
                status=404
            )

        serializer = SalaryStructureAdminUpdateSerializer(
            salary_structure,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(
                {"error": 1, "message": "Validation failed", "errors": serializer.errors},
                status=400
            )

        serializer.save(updated_by=user)
        updated = serializer.instance

        return Response(
            {
                "error": 0,
                "message": "Salary structure updated successfully",
                "data": {
                    "id": updated.id,
                    "resolved_by": resolved_by,
                    "employee_id": updated.employee.employee_id,
                    "basic_salary": str(updated.basic_salary),
                    "hra": str(updated.hra),
                    "medical_allowance": str(updated.medical_allowance),
                    "conveyance_allowance": str(updated.conveyance_allowance),
                    "special_allowance": str(updated.special_allowance),
                    "epf": str(updated.epf),
                    "tds": str(updated.tds),
                    "is_active": updated.is_active,
                }
            },
            status=200
        )

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
