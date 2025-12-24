# """
# Custom permissions for Employee module.
# """

# from rest_framework import permissions


# class IsHROrAdmin(permissions.BasePermission):
#     """Only HR or Admin can perform this action"""
#     message = "Only HR or Admin can perform this action."

#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
#         return request.user.is_staff or request.user.is_superuser


# class IsOwnerOrHRAdmin(permissions.BasePermission):
#     """
#     Employee can view/edit their own data.
#     HR/Admin can view/edit all data.
#     """
#     message = "You can only access your own data."

#     def has_object_permission(self, request, view, obj):
#         if not request.user.is_authenticated:
#             return False
        
#         # HR/Admin can access all
#         if request.user.is_staff or request.user.is_superuser:
#             return True
        
#         # Employee can access their own data
#         if hasattr(request.user, 'employee'):
#             return obj.id == request.user.employee.id
        
#         return False


# class CanViewEmployee(permissions.BasePermission):
#     """
#     Determine who can view employee data:
#     - Everyone can view basic list
#     - Manager can view their reportees
#     - HR/Admin can view all
#     """
    
#     def has_permission(self, request, view):
#         return request.user.is_authenticated

#     def has_object_permission(self, request, view, obj):
#         if not request.user.is_authenticated:
#             return False
        
#         # HR/Admin can view all
#         if request.user.is_staff or request.user.is_superuser:
#             return True
        
#         # Employee can view their own
#         if hasattr(request.user, 'employee'):
#             if obj.id == request.user.employee.id:
#                 return True
            
#             # Manager can view reportees
#             if obj.reporting_manager_id == request.user.employee.id:
#                 return True
        
#         # For safe methods, allow viewing colleagues in same department
#         if request.method in permissions.SAFE_METHODS:
#             if hasattr(request.user, 'employee'):
#                 return obj.department_id == request.user.employee.department_id
        
#         return False


# class CanEditRelatedData(permissions.BasePermission):
#     """
#     Permission for editing emergency contacts, education, work history.
#     - Employee can add to their own profile (but not delete for documents)
#     - HR/Admin can add/edit/delete all
#     """
    
#     def has_permission(self, request, view):
#         return request.user.is_authenticated

#     def has_object_permission(self, request, view, obj):
#         if not request.user.is_authenticated:
#             return False
        
#         # HR/Admin can do anything
#         if request.user.is_staff or request.user.is_superuser:
#             return True
        
#         # Employee can only edit their own related data
#         if hasattr(request.user, 'employee'):
#             # obj.employee is the related employee
#             if hasattr(obj, 'employee'):
#                 return obj.employee.id == request.user.employee.id
        
#         return False
