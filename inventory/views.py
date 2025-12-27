from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Count, Q

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
    DeviceTypeDropdownSerializer,
    DeviceListSerializer,
    DeviceDetailSerializer,
    DeviceCreateUpdateSerializer,
    DeviceAssignmentSerializer,
    DeviceAssignmentActionSerializer
)
from .permissions import (
    IsAdminManagerOrHR,
    CanViewAllDevices,
    CanManageDevices,
    CanAssignDevices
)


class DeviceTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Device Type management
    
    Permissions:
    - List/Retrieve: All authenticated users (for dropdowns)
    - Create/Update/Delete: Admin, Manager, HR only
    
    Query Parameters for list:
    - format=dropdown: Returns only id and name fields
    - is_active=true/false: Filter by active status
    """
    queryset = DeviceType.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']
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
            # Check if dropdown format is requested
            if self.request.query_params.get('format') == 'dropdown':
                return DeviceTypeDropdownSerializer
            return DeviceTypeListSerializer
        return DeviceTypeSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to handle dropdown format"""
        # If dropdown format requested, return simplified data
        if request.query_params.get('format') == 'dropdown':
            device_types = self.get_queryset().filter(is_active=True).values('id', 'name')
            return Response({
                "error": 0,
                "data": list(device_types)
            })
        
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'destroy']:
            return [IsAuthenticated(), IsAdminManagerOrHR()]
        # Everyone can view device types (for dropdowns)
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        """Soft delete device type"""
        instance.is_active = False
        instance.save()

    # REMOVED: devices action - now use GET /api/inventory/devices/?device_type={id}
    # REMOVED: stats action - stats are already included in the detail response (DeviceTypeSerializer)


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Device management
    
    Permissions:
    - List/Retrieve all devices: Admin, Manager, HR only
    - Create/Update/Delete: Admin, Manager, HR only
    - Assign/Unassign: Admin, Manager, HR only
    - My Devices/My History: All authenticated employees (own devices only)
    
    Query Parameters for list:
    - assigned=true/false: Filter by assignment status
    - status=working/maintenance/etc: Filter by device status
    - condition=good/fair/etc: Filter by device condition
    - device_type=<id>: Filter by device type
    - employee=<id> or employee=me: Filter by employee (use 'me' for current user)
    - my_devices=true: Filter to current user's devices (alias for employee=me)
    - warranty_expiring=true: Filter devices with warranty expiring in next 30 days
    - warranty_expiry__lte=<date>: Filter by warranty expiry date (ISO format)
    - warranty_expiry__gte=<date>: Filter by warranty expiry date (ISO format)
    """
    queryset = Device.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = [
        'device_type', 'status', 'condition', 'is_active', 'employee'
    ] if HAS_DJANGO_FILTER else []
    search_fields = [
        'serial_number', 'internal_serial_number', 'model_name', 'brand',
        'device_type__name', 'notes',
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
        """Filter queryset based on user permissions and query parameters"""
        queryset = super().get_queryset().select_related(
            'device_type', 'employee', 'created_by', 'updated_by'
        )
        
        # Show only active devices for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        # Handle 'my_devices' query parameter - filter to current user's devices
        my_devices = self.request.query_params.get('my_devices')
        if my_devices and my_devices.lower() == 'true':
            if hasattr(self.request.user, 'employee'):
                queryset = queryset.filter(employee=self.request.user.employee)
            else:
                queryset = queryset.none()  # Return empty if no employee profile
        
        # Handle 'employee=me' query parameter
        employee_param = self.request.query_params.get('employee')
        if employee_param == 'me':
            if hasattr(self.request.user, 'employee'):
                queryset = queryset.filter(employee=self.request.user.employee)
            else:
                queryset = queryset.none()
        
        # Additional filters from query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        assigned = self.request.query_params.get('assigned')
        if assigned:
            if assigned.lower() == 'true':
                queryset = queryset.filter(employee__isnull=False)
            elif assigned.lower() == 'false':
                queryset = queryset.filter(employee__isnull=True)
        
        # Handle warranty expiring filter
        warranty_expiring = self.request.query_params.get('warranty_expiring')
        if warranty_expiring and warranty_expiring.lower() == 'true':
            from datetime import timedelta
            today = timezone.now().date()
            next_30_days = today + timedelta(days=30)
            queryset = queryset.filter(
                warranty_expiry__gte=today,
                warranty_expiry__lte=next_30_days,
                is_active=True
            ).order_by('warranty_expiry')
        
        # Handle warranty expiry date range filters
        warranty_expiry_lte = self.request.query_params.get('warranty_expiry__lte')
        if warranty_expiry_lte:
            try:
                from datetime import datetime
                expiry_date = datetime.fromisoformat(warranty_expiry_lte.replace('Z', '+00:00')).date()
                queryset = queryset.filter(warranty_expiry__lte=expiry_date)
            except (ValueError, AttributeError):
                pass  # Ignore invalid date formats
        
        warranty_expiry_gte = self.request.query_params.get('warranty_expiry__gte')
        if warranty_expiry_gte:
            try:
                from datetime import datetime
                expiry_date = datetime.fromisoformat(warranty_expiry_gte.replace('Z', '+00:00')).date()
                queryset = queryset.filter(warranty_expiry__gte=expiry_date)
            except (ValueError, AttributeError):
                pass  # Ignore invalid date formats
        
        return queryset

    def get_permissions(self):
        """
        Set permissions based on action
        
        - CRUD operations: Admin/Manager/HR only
        - Assign/Unassign: Admin/Manager/HR only
        - List/Retrieve all: Admin/Manager/HR only (unless filtering to own devices)
        - My devices/history: All authenticated (filtered to own)
        """
        # CRUD operations - Admin/Manager/HR only
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageDevices()]
        
        # Assignment action (assign/unassign) - Admin/Manager/HR only
        if self.action in ['assignment']:
            return [IsAuthenticated(), CanAssignDevices()]
        
        # List/Retrieve - Check if user is filtering to own devices
        if self.action in ['list', 'retrieve']:
            # If filtering to own devices, allow all authenticated users
            if (self.request.query_params.get('my_devices') == 'true' or 
                self.request.query_params.get('employee') == 'me'):
                return [IsAuthenticated()]
            # Otherwise, require admin/manager/hr
            return [IsAuthenticated(), CanViewAllDevices()]
        
        # Other admin actions - Admin/Manager/HR only
        if self.action in ['assignment_history']:
            return [IsAuthenticated(), IsAdminManagerOrHR()]
        
        # My history - All authenticated employees
        if self.action in ['my_assignment_history']:
            return [IsAuthenticated()]
        
        # Default - just authenticated
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

    # ═══════════════════════════════════════════════════════════
    # REMOVED ENDPOINTS - Now handled via query parameters:
    # - my-devices: Use ?my_devices=true or ?employee=me
    # - unassigned: Use ?assigned=false
    # - warranty-expiring: Use ?warranty_expiring=true
    # ═══════════════════════════════════════════════════════════

    @action(detail=False, methods=['get'], url_path='my-history')
    def my_assignment_history(self, request):
        """
        Get device assignment history for logged-in employee
        GET /api/inventory/devices/my-history/
        
        Permission: All authenticated employees
        Returns: Only assignment history for the requesting user
        
        Note: This endpoint is kept separate as it returns assignment history,
        not device list, so it can't be consolidated into the list endpoint.
        """
        user = request.user
        
        if not hasattr(user, 'employee'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        assignments = DeviceAssignment.objects.filter(
            employee=user.employee
        ).select_related(
            'device', 'device__device_type', 'assigned_by'
        ).order_by('-assigned_date')
        
        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })

    # ═══════════════════════════════════════════════════════════
    # ADMIN/MANAGER/HR ONLY ENDPOINTS
    # ═══════════════════════════════════════════════════════════

    @action(detail=True, methods=['post'], url_path='assignment')
    def assignment(self, request, pk=None):
        """
        Assign or unassign device to/from an employee
        POST /api/inventory/devices/{id}/assignment/
        
        To assign: Body: {"employee": 1, "notes": "...", "condition": "good"}
        To unassign: Body: {"employee": null, "notes": "...", "condition": "good"}
                      or: Body: {"notes": "...", "condition": "good"}
        
        Permission: Admin, Manager, HR only
        """
        device = self.get_object()
        
        if not device.is_active:
            return Response({
                "error": 1,
                "message": "Cannot modify assignment for inactive device."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = DeviceAssignmentActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": 1,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = serializer.validated_data.get('employee')
        notes = serializer.validated_data.get('notes', '')
        condition = serializer.validated_data.get('condition', device.condition)

        # ASSIGN: If employee is provided
        if employee is not None:
            if device.employee:
                return Response({
                    "error": 1,
                    "message": f"Device is already assigned to {device.employee.get_full_name()}. Please unassign first."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create assignment record
            assignment = DeviceAssignment.objects.create(
                device=device,
                employee=employee,
                assigned_by=request.user,
                condition_at_assignment=condition,
                notes=notes
            )

            # Update device
            device.employee = employee
            device.condition = condition
            device.updated_by = request.user
            device.save()

            return Response({
                "error": 0,
                "data": {
                    "message": f"Device assigned to {employee.get_full_name()} successfully",
                    "assignment": DeviceAssignmentSerializer(assignment).data
                }
            }, status=status.HTTP_201_CREATED)
        
        # UNASSIGN: If employee is None or not provided
        else:
            if not device.employee:
                return Response({
                    "error": 1,
                    "message": "Device is not assigned to any employee."
                }, status=status.HTTP_400_BAD_REQUEST)

            previous_employee = device.employee

            # Update the most recent active assignment
            assignment = DeviceAssignment.objects.filter(
                device=device,
                employee=device.employee,
                returned_date__isnull=True
            ).order_by('-assigned_date').first()

            if assignment:
                assignment.returned_date = timezone.now()
                assignment.returned_to = request.user
                assignment.condition_at_return = condition
                if notes:
                    assignment.notes = f"{assignment.notes}\nReturn notes: {notes}" if assignment.notes else f"Return notes: {notes}"
                assignment.save()

            # Update device
            device.employee = None
            device.condition = condition
            device.updated_by = request.user
            device.save()

            return Response({
                "error": 0,
                "data": {
                    "message": f"Device unassigned from {previous_employee.get_full_name()} successfully"
                }
            }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def assignment_history(self, request, pk=None):
        """
        Get assignment history for a specific device (with pagination support)
        
        Query Parameters:
        - limit: Number of records to return (default: all)
        - offset: Number of records to skip (for pagination)
        
        Permission: Admin, Manager, HR only
        
        Note: Assignment history is also included in the device detail response,
        but this endpoint provides pagination and filtering capabilities.
        """
        device = self.get_object()
        assignments = DeviceAssignment.objects.filter(
            device=device
        ).select_related(
            'employee', 'assigned_by', 'returned_to'
        ).order_by('-assigned_date')
        
        # Support pagination via query parameters
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset')
        
        if limit:
            try:
                limit = int(limit)
                if offset:
                    offset = int(offset)
                    assignments = assignments[offset:offset+limit]
                else:
                    assignments = assignments[:limit]
            except ValueError:
                pass  # Ignore invalid limit/offset values
        
        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })
    
    # REMOVED: unassigned_devices action - now use ?assigned=false
    # REMOVED: warranty_expiring action - now use ?warranty_expiring=true


class InventoryDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for inventory dashboard statistics
    
    Permission: Admin, Manager, HR only
    """
    permission_classes = [IsAuthenticated, IsAdminManagerOrHR]

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Get dashboard summary with all device types and their statistics
        GET /api/inventory/dashboard/summary/
        """
        device_types = DeviceType.objects.filter(is_active=True).order_by('name')
        
        device_types_data = []
        total_devices = 0
        total_assigned = 0
        total_unassigned = 0
        
        for device_type in device_types:
            total = device_type.total_devices
            working = device_type.working_devices
            assigned = device_type.assigned_devices
            unassigned = device_type.unassigned_devices
            
            total_devices += total
            total_assigned += assigned
            total_unassigned += unassigned
            
            device_types_data.append({
                'id': device_type.id,
                'name': device_type.name,
                'description': device_type.description,
                'total': total,
                'working': working,
                'assigned': assigned,
                'unassigned': unassigned,
            })
        
        # Get status breakdown
        status_breakdown = Device.objects.filter(
            is_active=True
        ).values('status').annotate(
            count=Count('id')
        ).order_by('status')

        return Response({
            "error": 0,
            "data": {
                'total_devices': total_devices,
                'total_assigned': total_assigned,
                'total_unassigned': total_unassigned,
                'device_types': device_types_data,
                'status_breakdown': list(status_breakdown)
            }
        })
    

