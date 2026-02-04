from rest_framework import filters
from django.db.models import Q

class HierarchyFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own records or their subordinates' records.
    Admin/Staff users can see everything.
    
    This filter respects 'userid' or 'employee_id' in query params,
    validating against the user's hierarchy.
    """
    def filter_queryset(self, request, queryset, view):
        user = request.user
        
        # Staff/Superuser → all access
        if user.is_staff or user.is_superuser:
            target_id = request.query_params.get('userid') or request.query_params.get('employee_id')
            if target_id:
                return queryset.filter(Q(employee_id=target_id) | Q(id=target_id) if queryset.model.__name__ == 'Employee' else Q(employee_id=target_id))
            return queryset
            
        if not hasattr(user, 'employee_profile'):
            return queryset.none()
            
        employee = user.employee_profile
        target_id = request.query_params.get('userid') or request.query_params.get('employee_id')
        
        # If the queryset is for the Employee model itself
        if queryset.model.__name__ == 'Employee':
            if target_id:
                # Can only see self or direct subordinate
                if str(target_id) == str(employee.id):
                    return queryset.filter(id=employee.id)
                if employee.can_view_subordinates():
                    return queryset.filter(id=target_id, reporting_manager_id=employee.id)
                return queryset.none()
            
            # Default list: self + subordinates
            q = Q(id=employee.id)
            if employee.can_view_subordinates():
                q |= Q(reporting_manager_id=employee.id)
            return queryset.filter(q)
        
        # For other models, look for an 'employee' field
        if hasattr(queryset.model, 'employee'):
            if target_id:
                # Can only see self or direct subordinate
                if str(target_id) == str(employee.id):
                    return queryset.filter(employee_id=employee.id)
                if employee.can_view_subordinates():
                    # Double check the employee exists and is a subordinate
                    return queryset.filter(employee_id=target_id, employee__reporting_manager_id=employee.id)
                return queryset.none()
            
            # Default list: self + subordinates
            q = Q(employee_id=employee.id)
            if employee.can_view_subordinates():
                sub_ids = employee.get_subordinate_ids()
                q |= Q(employee_id__in=sub_ids)
            return queryset.filter(q)
            
        return queryset
