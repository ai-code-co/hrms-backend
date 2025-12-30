from rest_framework.permissions import BasePermission, SAFE_METHODS


class AttendanceObjectPermission(BasePermission):
    """
    Attendance permissions:

    Employee  → self only
    Manager   → reportees (read-only)
    HR/Admin  → full access
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # HR / Admin → everything
        if user.is_staff or user.is_superuser:
            return True

        # Must have employee profile
        if not hasattr(user, "employee_profile"):
            return False

        employee = user.employee_profile

        # Employee → own attendance
        if obj.employee_id == employee.id:
            return True

        # Manager → view reportees only (READ-ONLY)
        if request.method in SAFE_METHODS:
            return obj.employee.reporting_manager_id == employee.id

        return False
