"""
Custom permissions for Inventory module

Permission Levels (based on designation.level):
- Level 1: C-Level (CEO, CTO, CFO)
- Level 2: Director/VP
- Level 3: Manager/HR
- Level 4: Team Lead
- Level 5: Senior Staff
- Level 6: Junior Staff
- Level 7: Trainee/Intern

Admin, Manager, HR (level <= 3) can manage devices.
Regular employees (level > 3) can only view their own devices.
"""

from rest_framework.permissions import BasePermission


class IsAdminManagerOrHR(BasePermission):
    """
    Permission for Admin, Manager, or HR users.
    
    Allows access if:
    1. User is superuser, OR
    2. User is staff (is_staff=True), OR
    3. User's designation level is 1, 2, or 3 (C-Level, Director, Manager/HR)
    """
    message = "Only Admin, Manager, or HR can perform this action."
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        # Superuser or staff can always access
        if user.is_superuser or user.is_staff:
            return True
        
        # Check employee designation level
        if hasattr(user, 'employee_profile') and user.employee_profile:
            employee = user.employee_profile
            if employee.designation and employee.designation.level:
                # Level 1-3 are Admin/Director/Manager/HR
                return employee.designation.level <= 3
        
        return False


class CanViewAllDevices(BasePermission):
    """
    Permission to view all devices in the system.
    
    Only Admin, Manager, HR can view all devices.
    Regular employees should use /my-devices/ endpoint instead.
    """
    message = "You don't have permission to view all devices. Use /my-devices/ endpoint."
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        # Superuser or staff can view all
        if user.is_superuser or user.is_staff:
            return True
        
        # Check employee designation level
        if hasattr(user, 'employee_profile') and user.employee_profile:
            employee = user.employee_profile
            if employee.designation and employee.designation.level:
                # Level 1-3 can view all devices
                return employee.designation.level <= 3
        
        return False


class CanManageDevices(BasePermission):
    """
    Permission to create, update, delete devices.
    Same as IsAdminManagerOrHR but with different message.
    """
    message = "Only Admin, Manager, or HR can manage devices."
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        if user.is_superuser or user.is_staff:
            return True
        
        if hasattr(user, 'employee_profile') and user.employee_profile:
            employee = user.employee_profile
            if employee.designation and employee.designation.level:
                return employee.designation.level <= 3
        
        return False


class CanAssignDevices(BasePermission):
    """
    Permission to assign/unassign devices to employees.
    """
    message = "Only Admin, Manager, or HR can assign/unassign devices."
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        if user.is_superuser or user.is_staff:
            return True
        
        if hasattr(user, 'employee_profile') and user.employee_profile:
            employee = user.employee_profile
            if employee.designation and employee.designation.level:
                return employee.designation.level <= 3
        
        return False
