from rest_framework.permissions import BasePermission, SAFE_METHODS


class EmployeeObjectPermission(BasePermission):
    """
    Permission based on Role system:
    - Admin/HR → full access (can_view_all_employees, can_edit_all_employees)
    - Manager → can view/edit subordinates (can_view_subordinates)
    - Employee → self only
    """
    def has_permission(self, request, view):
        """Check if user has permission for the view action"""
        if not request.user.is_authenticated:
            return False
        
        # Superuser and staff always have permission
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # For list/create actions, check if user has employee profile
        if view.action in ['list', 'create']:
            return hasattr(request.user, 'employee_profile')
        
        # For other actions, object-level permission will be checked
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user

        # Backward compatibility: Superuser always has access
        if user.is_superuser:
            return True

        # Must have employee profile
        if not hasattr(user, "employee_profile"):
            return False

        employee = user.employee_profile

        # Self access - everyone can access their own profile
        if obj.id == employee.id:
            return True

        # Check role-based permissions
        if employee.role:
            # Admin/HR can view/edit all employees
            if employee.role.can_view_all_employees:
                # For edit operations, check can_edit_all_employees
                if request.method not in SAFE_METHODS:
                    return employee.role.can_edit_all_employees
                return True

            # Manager can view subordinates (read-only)
            if employee.role.can_view_subordinates and request.method in SAFE_METHODS:
                return obj.reporting_manager_id == employee.id

        # Backward compatibility: is_staff has admin-like access
        if user.is_staff:
            return True

        # Default: no access
        return False
