from rest_framework import viewsets, status, filters
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

from django.db.models import Q
from .models import Employee, EmergencyContact, Education, WorkHistory
from .serializers import (
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    EmployeeCreateUpdateSerializer,
    EmergencyContactSerializer,
    EducationSerializer,
    WorkHistorySerializer
)


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
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = [
        'department', 'designation', 'employment_status', 
        'employee_type', 'is_active'
    ] if HAS_DJANGO_FILTER else []
    search_fields = [
        'employee_id', 'first_name', 'last_name', 'email', 
        'phone', 'pan_number', 'aadhar_number'
    ]
    ordering_fields = [
        'employee_id', 'first_name', 'last_name', 
        'joining_date', 'created_at'
    ]
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admin/Staff can see all employees
        if user.is_staff:
            return queryset
        
        # Regular users can only see active employees
        queryset = queryset.filter(is_active=True)
        
        # If user has employee profile, they can see their own data
        if hasattr(user, 'employee_profile'):
            return queryset
        
        return queryset
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Set created_by when creating employee"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating employee"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current logged-in user's employee profile"""
        if not hasattr(request.user, 'employee_profile'):
            return Response(
                {'detail': 'No employee profile found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        employee = request.user.employee_profile
        serializer = EmployeeDetailSerializer(employee)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subordinates(self, request, pk=None):
        """Get all subordinates of an employee"""
        employee = self.get_object()
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
        serializer = EmergencyContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='educations')
    def add_education(self, request, pk=None):
        """Add education record to employee"""
        employee = self.get_object()
        serializer = EducationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='work-histories')
    def add_work_history(self, request, pk=None):
        """Add work history to employee"""
        employee = self.get_object()
        serializer = WorkHistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Emergency Contact management"""
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = ['employee', 'is_primary'] if HAS_DJANGO_FILTER else []
    search_fields = ['name', 'phone', 'relationship']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]


class EducationViewSet(viewsets.ModelViewSet):
    """ViewSet for Education management"""
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = ['employee', 'level', 'is_completed'] if HAS_DJANGO_FILTER else []
    search_fields = ['degree', 'institution', 'field_of_study']
    ordering_fields = ['end_date', 'start_date']
    ordering = ['-end_date']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]


class WorkHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Work History management"""
    queryset = WorkHistory.objects.all()
    serializer_class = WorkHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = ['employee', 'is_current'] if HAS_DJANGO_FILTER else []
    search_fields = ['company_name', 'job_title']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-end_date', '-start_date']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
