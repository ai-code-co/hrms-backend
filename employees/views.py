from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter


# Optional django-filter import
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False

from .models import Employee, EmergencyContact, Education, WorkHistory
from .serializers import (
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    EmployeeCreateUpdateSerializer,
    EmergencyContactSerializer,
    EducationSerializer,
    WorkHistorySerializer,
    EmployeeAdminDetailSerializer,
    EmployeeSelfDetailSerializer,
    EmployeeManagerDetailSerializer,
)

from .permissions import EmployeeObjectPermission
from rest_framework.exceptions import PermissionDenied



class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Employee management
    
    list: Get all employees (with filters and search)
    retrieve: Get single employee details with all related data
    create: Create new employee (Admin/HR only)
    update: Update employee (Admin/HR only)
    destroy: Soft delete employee (Admin only)
    """
    queryset = Employee.objects.all()
    permission_classes = [IsAuthenticated, EmployeeObjectPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = [
        'department', 'designation', 'employment_status', 
        'employee_type', 'is_active'
    ] if HAS_DJANGO_FILTER else []
    search_fields = [
        'employee_id',
        'first_name',
        'last_name',
        'email',
        'phone',
    ]
    ordering_fields = [
        'employee_id', 'first_name', 'last_name', 
        'joining_date', 'created_at'
    ]
    ordering = ['-created_at']
    
    # def get_serializer_class(self):
    #     """Use different serializers based on action"""
    #     if self.action == 'list':
    #         return EmployeeListSerializer
    #     elif self.action in ['create', 'update', 'partial_update']:
    #         return EmployeeCreateUpdateSerializer
    #     return EmployeeDetailSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return EmployeeListSerializer

        if self.action in ["create", "update", "partial_update"]:
            return EmployeeCreateUpdateSerializer

        # Detail views (retrieve, me)
        user = self.request.user

        # Superuser always gets admin serializer
        if user.is_superuser:
            return EmployeeAdminDetailSerializer

        # Check role-based access
        if hasattr(user, "employee_profile"):
            employee = user.employee_profile
            
            # Admin/HR → full access
            if employee.role and employee.role.can_view_all_employees:
                return EmployeeAdminDetailSerializer

            # For retrieve action, check if viewing self or reportee
            if self.action == "retrieve":
                try:
                    pk = self.kwargs.get('pk')
                    if pk:
                        # Check if viewing self
                        if str(employee.id) == str(pk):
                            return EmployeeSelfDetailSerializer
                        # Check if viewing reportee
                        from .models import Employee
                        try:
                            obj = Employee.objects.get(pk=pk)
                            if obj.reporting_manager_id == employee.id:
                                return EmployeeManagerDetailSerializer
                        except Employee.DoesNotExist:
                            pass
                except (KeyError, ValueError, TypeError) as e:
                    # Log error if needed, but continue with default serializer
                    pass

            # Default for me action or fallback
            return EmployeeSelfDetailSerializer

        # Backward compatibility: is_staff gets admin serializer
        if user.is_staff:
            return EmployeeAdminDetailSerializer

        # Manager → reportees (fallback)
        return EmployeeManagerDetailSerializer





    def get_queryset(self):
        user = self.request.user

        # Superuser always has access
        if user.is_superuser:
            return Employee.objects.all()

        # Check role-based access
        if hasattr(user, "employee_profile"):
            employee = user.employee_profile
            
            # Admin/HR → can list all employees
            if employee.role and employee.role.can_view_all_employees:
                return Employee.objects.all()
            
            # Manager → can list subordinates
            if employee.role and employee.role.can_view_subordinates:
                return Employee.objects.filter(
                    reporting_manager=employee,
                    is_active=True
                )

        # Backward compatibility: is_staff can list all
        if user.is_staff:
            return Employee.objects.all()

        # Employee & others → NO list access
        return Employee.objects.none()
    

    def perform_create(self, serializer):
        user = self.request.user
        
        # Superuser always allowed
        if user.is_superuser:
            serializer.save(
                created_by=user,
                updated_by=user
            )
            return

        # Check role-based permission
        if hasattr(user, "employee_profile") and user.employee_profile.role:
            if user.employee_profile.role.can_create_employees:
                serializer.save(
                    created_by=user,
                    updated_by=user
                )
                return

        # Backward compatibility: is_staff allowed
        if user.is_staff:
            serializer.save(
                created_by=user,
                updated_by=user
            )
            return

        raise PermissionDenied("You do not have permission to create employees.")
    

    def perform_update(self, serializer):
        user = self.request.user
        employee = serializer.instance
        
        # Superuser always allowed
        if user.is_superuser:
            serializer.save(updated_by=user)
            return

        # Check role-based permission
        if hasattr(user, "employee_profile"):
            user_employee = user.employee_profile
            
            # Admin/HR can edit anyone
            if user_employee.role and user_employee.role.can_edit_all_employees:
                serializer.save(updated_by=user)
                return
            
            # Employee can edit self
            if employee and employee.id == user_employee.id:
                serializer.save(updated_by=user)
                return

        # Backward compatibility: is_staff allowed
        if user.is_staff:
            serializer.save(updated_by=user)
            return

        raise PermissionDenied("You do not have permission to update this employee.")



    def _can_edit_employee(self, request, employee):
        user = request.user
        
        # Superuser always allowed
        if user.is_superuser:
            return True

        # Check role-based permission
        if hasattr(user, "employee_profile"):
            user_employee = user.employee_profile
            
            # Admin/HR can edit anyone
            if user_employee.role and user_employee.role.can_edit_all_employees:
                return True

            # Employee can edit self only
            if employee.id == user_employee.id:
                return True

        # Backward compatibility: is_staff allowed
        if user.is_staff:
            return True

        return False


    def destroy(self, request, *args, **kwargs):
        """Soft delete by marking is_active=False"""
        user = request.user
        
        # Superuser always allowed
        if user.is_superuser:
            pass  # Allow
        # Check role-based permission
        elif hasattr(user, "employee_profile") and user.employee_profile.role:
            if not user.employee_profile.role.can_delete_employees:
                raise PermissionDenied("You do not have permission to delete employees.")
        # Backward compatibility: is_staff allowed
        elif not user.is_staff:
            raise PermissionDenied("You do not have permission to delete employees.")

        employee = self.get_object()
        employee.is_active = False
        employee.updated_by = user
        employee.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current logged-in user's employee profile"""
        if not hasattr(request.user, 'employee_profile'):
            return Response(
                {'detail': 'No employee profile found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        employee = request.user.employee_profile
        serializer = EmployeeSelfDetailSerializer(employee)
        return Response(serializer.data)
    
    # @action(detail=True, methods=['get'])
    # def subordinates(self, request, pk=None):
    #     """Get all subordinates of an employee"""
    #     employee = self.get_object()
    #     subordinates = Employee.objects.filter(
    #         reporting_manager=employee,
    #         is_active=True
    #     )
    #     serializer = EmployeeListSerializer(subordinates, many=True)
    #     return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subordinates(self, request, pk=None):
        """
        Get subordinates of an employee.
        Rules:
        - HR/Admin → can view subordinates of anyone
        - Manager  → can view ONLY their own subordinates
        - Employee → not allowed
        """
        employee = self.get_object()
        user = request.user

        # Superuser always allowed
        if user.is_superuser:
            pass
        # Check role-based permission
        elif hasattr(user, "employee_profile"):
            user_employee = user.employee_profile
            
            # Admin/HR → allowed for all
            if user_employee.role and user_employee.role.can_view_all_employees:
                pass
            # Manager → only own subordinates
            elif user_employee.role and user_employee.role.can_view_subordinates:
                if employee.id != user_employee.id:
                    raise PermissionDenied(
                        "You can only view your own subordinates."
                    )
            else:
                raise PermissionDenied("You are not allowed to view subordinates.")
        # Backward compatibility: is_staff allowed
        elif user.is_staff:
            pass
        # Everyone else → forbidden
        else:
            raise PermissionDenied("You are not allowed to view subordinates.")

        subordinates = Employee.objects.filter(
            reporting_manager=employee,
            is_active=True
        )

        serializer = EmployeeListSerializer(subordinates, many=True)
        return Response(serializer.data)

    
    @action(detail=True, methods=['post'], url_path='emergency-contacts')
    def add_emergency_contact(self, request, pk=None):
        """Add emergency contact to employee"""
        employee = self.get_object()
        if not self._can_edit_employee(request, employee):
            return Response(
                {"detail": "You do not have permission to modify this employee."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = EmergencyContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                employee=employee,
                created_by=request.user,
                updated_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='educations')
    def add_education(self, request, pk=None):
        """Add education record to employee"""
        employee = self.get_object()
        if not self._can_edit_employee(request, employee):
            return Response(
                {"detail": "You do not have permission to modify this employee."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = EducationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                employee=employee,
                created_by=request.user,
                updated_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='work-histories')
    def add_work_history(self, request, pk=None):
        """Add work history to employee"""
        employee = self.get_object()
        if not self._can_edit_employee(request, employee):
            return Response(
                {"detail": "You do not have permission to modify this employee."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = WorkHistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                employee=employee,
                created_by=request.user,
                updated_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class EmergencyContactViewSet(viewsets.ModelViewSet):
#     """ViewSet for Emergency Contact management"""
#     queryset = EmergencyContact.objects.all()
#     serializer_class = EmergencyContactSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [SearchFilter]
#     if HAS_DJANGO_FILTER:
#         filter_backends.insert(0, DjangoFilterBackend)
#     filterset_fields = ['employee', 'is_primary'] if HAS_DJANGO_FILTER else []
#     search_fields = ['name', 'phone', 'relationship']
    
#     def get_permissions(self):
#         """Set permissions based on action"""
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             return [IsAuthenticated(), IsAdminUser()]
#         return [IsAuthenticated()]
class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    READ-ONLY.
    Create/Update/Delete must happen via EmployeeViewSet.
    """
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]


# class EducationViewSet(viewsets.ModelViewSet):
#     """ViewSet for Education management"""
#     queryset = Education.objects.all()
#     serializer_class = EducationSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [SearchFilter, OrderingFilter]
#     if HAS_DJANGO_FILTER:
#         filter_backends.insert(0, DjangoFilterBackend)
#     filterset_fields = ['employee', 'level', 'is_completed'] if HAS_DJANGO_FILTER else []
#     search_fields = ['degree', 'institution', 'field_of_study']
#     ordering_fields = ['end_date', 'start_date']
#     ordering = ['-end_date']
    
#     def get_permissions(self):
#         """Set permissions based on action"""
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             return [IsAuthenticated(), IsAdminUser()]
#         return [IsAuthenticated()]
class EducationViewSet(viewsets.ModelViewSet):
    """
    READ-ONLY.
    Create/Update/Delete must happen via EmployeeViewSet.
    """
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]


# class WorkHistoryViewSet(viewsets.ModelViewSet):
#     """ViewSet for Work History management"""
#     queryset = WorkHistory.objects.all()
#     serializer_class = WorkHistorySerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [SearchFilter, OrderingFilter]
#     if HAS_DJANGO_FILTER:
#         filter_backends.insert(0, DjangoFilterBackend)
#     filterset_fields = ['employee', 'is_current'] if HAS_DJANGO_FILTER else []
#     search_fields = ['company_name', 'job_title']
#     ordering_fields = ['start_date', 'end_date']
#     ordering = ['-end_date', '-start_date']
    
#     def get_permissions(self):
#         """Set permissions based on action"""
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             return [IsAuthenticated(), IsAdminUser()]
#         return [IsAuthenticated()]
class WorkHistoryViewSet(viewsets.ModelViewSet):
    """
    READ-ONLY.
    Create/Update/Delete must happen via EmployeeViewSet.
    """
    queryset = WorkHistory.objects.all()
    serializer_class = WorkHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]  # 🔒 LOCKED
