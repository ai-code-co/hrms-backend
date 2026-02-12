from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter

# Optional django-filter import
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False

from .models import Department, Designation
from .serializers import (
    DepartmentSerializer, 
    DepartmentListSerializer,
    DesignationSerializer
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department management
    
    list: Get all departments
    retrieve: Get single department details
    create: Create new department (Admin/HR only)
    update: Update department (Admin/HR only)
    destroy: Delete department (Admin only)
    """
    queryset = Department.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = ['is_active'] if HAS_DJANGO_FILTER else []
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Use different serializers for list and detail"""
        if self.action == 'list':
            return DepartmentListSerializer
        return DepartmentSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        # Show only active departments for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in a department"""
        department = self.get_object()
        from employees.models import Employee
        from employees.serializers import EmployeeListSerializer
        
        employees = Employee.objects.filter(
            department=department,
            is_active=True
        )
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def designations(self, request, pk=None):
        """Get all designations in a department"""
        department = self.get_object()
        designations = Designation.objects.filter(
            department=department,
            is_active=True
        )
        serializer = DesignationSerializer(designations, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })


class DesignationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Designation management
    
    list: Get all designations
    retrieve: Get single designation details
    create: Create new designation (Admin/HR only)
    update: Update designation (Admin/HR only)
    destroy: Delete designation (Admin only)
    """
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = ['department', 'is_active', 'level'] if HAS_DJANGO_FILTER else []
    search_fields = ['name', 'description', 'department__name']
    ordering_fields = ['name', 'level', 'created_at']
    ordering = ['department', 'level', 'name']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Manual filtering by department if provided in query params
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        # Show only active designations for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
