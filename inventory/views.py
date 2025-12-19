from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

# Optional django-filter import
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False

from .models import DeviceType, Device, DeviceAssignment
from .serializers import (
    DeviceTypeListSerializer,
    DeviceTypeSerializer,
    DeviceListSerializer,
    DeviceDetailSerializer,
    DeviceCreateUpdateSerializer,
    DeviceAssignmentSerializer,
    DeviceAssignSerializer,
    DeviceUnassignSerializer
)


class DeviceTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Device Type management
    
    list: Get all device types with statistics
    retrieve: Get single device type details
    create: Create new device type (Admin/HR only)
    update: Update device type (Admin/HR only)
    destroy: Delete device type (Admin only)
    """
    queryset = DeviceType.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = ['is_active'] if HAS_DJANGO_FILTER else []
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'list':
            return DeviceTypeListSerializer
        return DeviceTypeSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        # Show only active device types for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def devices(self, request, pk=None):
        """Get all devices of this device type"""
        device_type = self.get_object()
        devices = Device.objects.filter(
            device_type=device_type,
            is_active=True
        )
        serializer = DeviceListSerializer(devices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for this device type"""
        device_type = self.get_object()
        return Response({
            'id': device_type.id,
            'name': device_type.name,
            'total': device_type.total_devices,
            'working': device_type.working_devices,
            'unassigned': device_type.unassigned_devices,
        })


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Device management
    
    list: Get all devices with filters
    retrieve: Get single device details
    create: Create new device (Admin/HR only)
    update: Update device (Admin/HR only)
    destroy: Soft delete device (Admin only)
    """
    queryset = Device.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = [
        'device_type', 'status', 'is_active', 'employee'
    ] if HAS_DJANGO_FILTER else []
    search_fields = [
        'serial_number', 'device_type__name', 'notes',
        'employee__first_name', 'employee__last_name', 'employee__employee_id'
    ]
    ordering_fields = [
        'device_type__name', 'serial_number', 'status',
        'purchase_date', 'created_at'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'list':
            return DeviceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DeviceCreateUpdateSerializer
        return DeviceDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        # Show only active devices for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'assign', 'unassign']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Set created_by and updated_by when creating device"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        """Set updated_by when updating device"""
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete device"""
        instance.is_active = False
        instance.updated_by = self.request.user
        instance.save()

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign device to an employee (Admin/HR only)"""
        device = self.get_object()
        
        if not device.is_active:
            return Response(
                {'detail': 'Cannot assign inactive device.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DeviceAssignSerializer(data=request.data)
        if serializer.is_valid():
            employee = serializer.validated_data['employee']
            notes = serializer.validated_data.get('notes', '')

            # Create assignment record
            assignment = DeviceAssignment.objects.create(
                device=device,
                employee=employee,
                assigned_by=request.user,
                notes=notes
            )

            # Update device
            device.employee = employee
            device.updated_by = request.user
            device.save()

            return Response(
                DeviceAssignmentSerializer(assignment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unassign(self, request, pk=None):
        """Unassign device from employee (Admin/HR only)"""
        device = self.get_object()

        if not device.employee:
            return Response(
                {'detail': 'Device is not assigned to any employee.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DeviceUnassignSerializer(data=request.data)
        if serializer.is_valid():
            notes = serializer.validated_data.get('notes', '')

            # Update the most recent active assignment
            assignment = DeviceAssignment.objects.filter(
                device=device,
                employee=device.employee,
                returned_date__isnull=True
            ).order_by('-assigned_date').first()

            if assignment:
                assignment.returned_date = timezone.now()
                if notes:
                    assignment.notes = f"{assignment.notes}\nReturned: {notes}" if assignment.notes else f"Returned: {notes}"
                assignment.save()

            # Update device
            device.employee = None
            device.updated_by = request.user
            device.save()

            return Response(
                {'detail': 'Device unassigned successfully.'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def assignment_history(self, request, pk=None):
        """Get assignment history for a device"""
        device = self.get_object()
        assignments = DeviceAssignment.objects.filter(device=device).order_by('-assigned_date')
        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class InventoryDashboardView(viewsets.ViewSet):
    """
    ViewSet for inventory dashboard statistics
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Get dashboard summary with all device types and their statistics"""
        device_types = DeviceType.objects.filter(is_active=True).order_by('name')
        
        device_types_data = []
        total_devices = 0
        
        for device_type in device_types:
            total = device_type.total_devices
            working = device_type.working_devices
            unassigned = device_type.unassigned_devices
            total_devices += total
            
            device_types_data.append({
                'id': device_type.id,
                'name': device_type.name,
                'description': device_type.description,
                'total': total,
                'working': working,
                'unassigned': unassigned,
            })

        return Response({
            'total_devices': total_devices,
            'device_types': device_types_data
        })

