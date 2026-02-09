from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter


# Optional django-filter import
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False

from .models import Employee, EmergencyContact, Education, WorkHistory, EmployeeDocument
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
    EmployeeLookupSerializer,
    EmployeeDocumentSerializer,
)

from .permissions import EmployeeObjectPermission
from rest_framework.exceptions import PermissionDenied


from employees.filters import HierarchyFilterBackend

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Employee management
    
    list: Get all employees (with filters and search)
    retrieve: Get single employee details with all related data
    create: Create new employee (Admin/HR only)
    update: Update employee details
    destroy: Soft delete (Admin/HR only)
    """
    queryset = Employee.objects.all()
    permission_classes = [IsAuthenticated, EmployeeObjectPermission]
    filter_backends = [HierarchyFilterBackend, SearchFilter, OrderingFilter]
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
    #     # ... (omitted for brevity)

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
        """Queryset is filtered by HierarchyFilterBackend"""
        return super().get_queryset().select_related(
            'role', 'department', 'designation', 'reporting_manager'
        ).prefetch_related('emergency_contacts', 'educations', 'work_histories')
    


    @action(detail=False, methods=['get'], url_path='lookup-list')
    def lookup_list(self, request):
        """
        Get a lightweight list of employees for lookup selection.
        Admins/HR: All active employees
        Managers: Only direct reportees
        """
        user = request.user
        queryset = Employee.objects.filter(is_active=True)

        # Apply visibility filters
        is_admin_hr = user.is_superuser or user.is_staff
        if not is_admin_hr and hasattr(user, 'employee_profile'):
            emp = user.employee_profile
            if emp.role and emp.role.can_view_all_employees:
                is_admin_hr = True
            
        if not is_admin_hr:
            if hasattr(user, 'employee_profile'):
                emp = user.employee_profile
                if emp.role and emp.role.can_view_subordinates:
                    queryset = queryset.filter(reporting_manager=emp)
                else:
                    # Regular employees can't look up anyone else
                    return Response({
                        "error": 0,
                        "data": []
                    })
            else:
                return Response({"error": 0, "data": []})

        serializer = EmployeeLookupSerializer(queryset, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })

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

    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Get or update current logged-in user's employee profile or a specific employee if allowed"""
        user = request.user
        target_id = request.query_params.get('userid') or request.query_params.get('employee_id')
        
        # Determine which employee to show/edit
        if target_id:
            # Check permission: Admin, HR, or Manager of the target employee
            can_access = False
            if user.is_staff or user.is_superuser:
                can_access = True
            elif hasattr(user, 'employee_profile'):
                requesting_emp = user.employee_profile
                if requesting_emp.can_view_all_employees():
                    can_access = True
                elif str(requesting_emp.id) == str(target_id):
                    can_access = True
                elif requesting_emp.can_view_subordinates():
                    target_employee = Employee.objects.filter(id=target_id, reporting_manager_id=requesting_emp.id).first()
                    if target_employee:
                        can_access = True
            
            if not can_access:
                return Response({"error": 1, "message": "Permission denied"}, status=403)
                
            employee = get_object_or_404(Employee, id=target_id)
        else:
            if not hasattr(user, 'employee_profile'):
                return Response(
                    {'detail': 'No employee profile found for this user.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            employee = user.employee_profile
        
        if request.method == 'PATCH':
            # Check if allowed to edit
            if not self._can_edit_employee(request, employee):
                return Response({"error": 1, "message": "Permission denied to edit this profile"}, status=403)

            # Allow partial update
            serializer = EmployeeCreateUpdateSerializer(
                employee, 
                data=request.data, 
                partial=True
            )
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                
                # Determine detail serializer based on role (similar to get_serializer_class logic)
                detail_serializer = EmployeeSelfDetailSerializer(employee)
                # If admin or manager, they might see more fields
                if user.is_superuser or (hasattr(user, 'employee_profile') and user.employee_profile.can_view_all_employees()):
                    detail_serializer = EmployeeAdminDetailSerializer(employee)
                elif hasattr(user, 'employee_profile') and employee.reporting_manager_id == user.employee_profile.id:
                    detail_serializer = EmployeeManagerDetailSerializer(employee)

                return Response({
                    "success": True,
                    "message": "Profile updated successfully",
                    "data": detail_serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # GET request
        # Pick the right serializer based on permission context
        if user.is_superuser or (hasattr(user, 'employee_profile') and user.employee_profile.can_view_all_employees()):
            serializer = EmployeeAdminDetailSerializer(employee)
        elif hasattr(user, 'employee_profile') and employee.reporting_manager_id == user.employee_profile.id:
            serializer = EmployeeManagerDetailSerializer(employee)
        else:
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

    @action(detail=True, methods=['post'], url_path='documents')
    def add_document(self, request, pk=None):
        """Add a document to employee"""
        employee = self.get_object()
        if not self._can_edit_employee(request, employee):
            return Response(
                {"detail": "You do not have permission to modify this employee."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EmployeeDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                employee=employee,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='documents/(?P<doc_id>[^/.]+)')
    def delete_document(self, request, pk=None, doc_id=None):
        """Delete an employee document"""
        employee = self.get_object()
        if not self._can_edit_employee(request, employee):
            return Response(
                {"detail": "You do not have permission to modify this employee profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document = get_object_or_404(EmployeeDocument, pk=doc_id, employee=employee)
        document_type = document.get_document_type_display()
        document.delete()
        
        return Response({
            "success": True,
            "message": f"Document '{document_type}' deleted successfully."
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='verify-document/(?P<doc_id>[^/.]+)')
    def verify_document(self, request, pk=None, doc_id=None):
        """Verify an employee document (Admin/HR only)"""
        user = request.user
        # Check if user is Admin/HR
        is_admin_hr = user.is_superuser or user.is_staff
        if not is_admin_hr and hasattr(user, 'employee_profile'):
            if user.employee_profile.role and user.employee_profile.role.can_view_all_employees:
                is_admin_hr = True
        
        if not is_admin_hr:
            return Response({"error": 1, "message": "Permission denied. Only Admin/HR can verify documents."}, status=403)

        document = get_object_or_404(EmployeeDocument, pk=doc_id, employee_id=pk)
        
        from django.utils import timezone
        document.is_verified = request.data.get('is_verified', True)
        if document.is_verified:
            document.verified_at = timezone.now()
            document.verified_by = user
        else:
            document.verified_at = None
            document.verified_by = None
        
        document.save()
        
        return Response({
            "success": True,
            "message": f"Document {document.get_document_type_display()} verification status updated.",
            "data": EmployeeDocumentSerializer(document).data
        })

    @action(detail=True, methods=['post'], url_path='terminate')
    def terminate(self, request, pk=None):
        """
        Terminate an employee (SuperAdmin/HR only)
        """
        user = request.user
        if not (user.is_superuser or user.is_staff):
             return Response({"error": 1, "message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
             
        employee = self.get_object()
        
        # Payload can include termination_date, reason, etc.
        # But for now we just toggle status
        employee.employment_status = 'terminated'
        employee.is_active = False
        employee.updated_by = user
        employee.save()
        
        return Response({
            "error": 0,
            "message": f"Employee {employee.get_full_name()} has been terminated successfully."
        })

    @action(detail=False, methods=['get'], url_path='terminated-list')
    def terminated_list(self, request):
        """
        Get all terminated employees (SuperAdmin/HR only)
        """
        user = request.user
        if not (user.is_superuser or user.is_staff):
             return Response({"error": 1, "message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
             
        queryset = Employee.objects.filter(employment_status='terminated')
        serializer = EmployeeListSerializer(queryset, many=True)
        
        return Response({
            "error": 0,
            "data": serializer.data
        })


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    READ-ONLY.
    Create/Update/Delete must happen via EmployeeViewSet.
    """
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]



class EducationViewSet(viewsets.ModelViewSet):
    """
    READ-ONLY.
    Create/Update/Delete must happen via EmployeeViewSet.
    """
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]



class WorkHistoryViewSet(viewsets.ModelViewSet):
    """
    READ-ONLY.
    Create/Update/Delete must happen via EmployeeViewSet.
    """
    queryset = WorkHistory.objects.all()
    serializer_class = WorkHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]  # 🔒 LOCKED


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Employee Documents.
    Allows HR/Admin to list and filter all documents.
    """
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = ['employee', 'document_type', 'is_verified'] if HAS_DJANGO_FILTER else []
    search_fields = ['employee__first_name', 'employee__last_name', 'document_type']
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admin/HR can see all
        if user.is_superuser or user.is_staff:
            return queryset
        
        if hasattr(user, 'employee_profile'):
            emp = user.employee_profile
            # Role-based check
            if emp.role and emp.role.can_view_all_employees:
                return queryset
            
            # Regular employees only see their own docs
            return queryset.filter(employee=emp)
            
        return queryset.none()

    def perform_destroy(self, instance):
        """Check permission before deleting"""
        user = self.request.user
        can_delete = False
        
        if user.is_superuser or user.is_staff:
            can_delete = True
        elif hasattr(user, 'employee_profile'):
            emp = user.employee_profile
            # Owner can delete their own documents
            if instance.employee_id == emp.id:
                can_delete = True
            # Admin/HR role can delete
            elif emp.role and emp.role.can_view_all_employees:
                can_delete = True
        
        if not can_delete:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to delete this document.")
        
        instance.delete()
