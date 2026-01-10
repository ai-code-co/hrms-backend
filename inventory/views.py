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

from .models import DeviceType, Device, DeviceAssignment, DeviceComment
from .serializers import (
    DeviceTypeListSerializer,
    DeviceTypeSerializer,
    DeviceListSerializer,
    DeviceDetailSerializer,
    DeviceCreateUpdateSerializer,
    DeviceAssignmentSerializer,
    DeviceAssignSerializer,
    DeviceUnassignSerializer,
    DeviceCommentSerializer,
    DeviceSubmitAuditSerializer
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
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminManagerOrHR()]
        # Everyone can view device types (for dropdowns)
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        """Soft delete device type"""
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['get'])
    def devices(self, request, pk=None):
        """
        Get all devices of this device type
        Only Admin/Manager/HR can access
        """
        device_type = self.get_object()
        devices = Device.objects.filter(
            device_type=device_type,
            is_active=True
        ).select_related('employee')
        serializer = DeviceListSerializer(devices, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for this device type"""
        device_type = self.get_object()
        return Response({
            "error": 0,
            "data": {
                'id': device_type.id,
                'name': device_type.name,
                'total': device_type.total_devices,
                'working': device_type.working_devices,
                'assigned': device_type.assigned_devices,
                'unassigned': device_type.unassigned_devices,
            }
        })
    
    @action(detail=False, methods=['get'])
    def dropdown(self, request):
        """Get device types for dropdown (id, name only)"""
        device_types = self.get_queryset().filter(is_active=True).values('id', 'name')
        return Response({
            "error": 0,
            "data": list(device_types)
        })


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Device management
    
    Permissions:
    - List/Retrieve all devices: Admin, Manager, HR only
    - Create/Update/Delete: Admin, Manager, HR only
    - Assign/Unassign: Admin, Manager, HR only
    - My Devices/My History: All authenticated employees (own devices only)
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
        'serial_number', 'model_name', 'brand',
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
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset().select_related(
            'device_type', 'employee', 'created_by', 'updated_by'
        )
        
        # Show only active devices for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
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
        
        return queryset

    def get_permissions(self):
        """
        Set permissions based on action
        
        - CRUD operations: Admin/Manager/HR only
        - Assign/Unassign: Admin/Manager/HR only
        - List/Retrieve all: Admin/Manager/HR only
        - My devices/history: All authenticated (filtered to own)
        """
        # CRUD operations - Admin/Manager/HR only
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageDevices()]
        
        # Assign/Unassign - Admin/Manager/HR only
        if self.action in ['assign', 'unassign']:
            return [IsAuthenticated(), CanAssignDevices()]
        
        # List/Retrieve all devices - Admin/Manager/HR only
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), CanViewAllDevices()]
        
        # Other admin actions - Admin/Manager/HR only
        if self.action in ['assignment_history', 'unassigned_devices', 'warranty_expiring']:
            return [IsAuthenticated(), IsAdminManagerOrHR()]
        
        # My devices & My history - All authenticated employees
        # (These endpoints filter to own devices, so no special permission needed)
        if self.action in ['my_devices', 'my_assignment_history']:
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
    # EMPLOYEE SELF-SERVICE ENDPOINTS (All authenticated users)
    # ═══════════════════════════════════════════════════════════

    @action(detail=True, methods=['post'], url_path='submit-audit')
    def submit_audit(self, request, pk=None):
        """
        Submit a monthly inventory audit for an assigned device
        POST /api/inventory/devices/{id}/submit-audit/
        Body: {"comment": "...", "condition": "good", "status": "working"}
        """
        device = self.get_object()
        user = request.user

        # 1. Permission Check: Must be assigned to this employee
        if not hasattr(user, 'employee_profile') or device.employee != user.employee_profile:
            return Response({
                "error": 1,
                "message": "You can only audit devices currently assigned to you."
            }, status=status.HTTP_403_FORBIDDEN)

        # 2. Duplicate Check: Only one audit per month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        existing_audit = DeviceComment.objects.filter(
            device=device,
            employee=user.employee_profile,
            created_at__gte=start_of_month,
            comment__startswith='[Monthly Audit]'
        ).exists()

        if existing_audit:
            return Response({
                "error": 1,
                "message": f"You have already submitted an audit for this device ({device.serial_number}) this month."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Validate Data
        serializer = DeviceSubmitAuditSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": 1,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # 4. Process Audit
        comment_text = serializer.validated_data['comment']
        condition = serializer.validated_data['condition']
        status_val = serializer.validated_data['status']

        # Update device state
        device.condition = condition
        device.status = status_val
        device.updated_by = user
        device.save()

        # Create audit trail comment
        audit_comment = DeviceComment.objects.create(
            device=device,
            employee=user.employee_profile,
            comment=f"[Monthly Audit] {comment_text}"
        )

        return Response({
            "error": 0,
            "message": "Monthly audit submitted successfully. Device status updated.",
            "data": {
                "audit_id": audit_comment.id,
                "condition": device.get_condition_display(),
                "status": device.get_status_display()
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='my-devices')
    def my_devices(self, request):
        """
        Get devices assigned to the logged-in employee
        GET /api/inventory/devices/my-devices/
        
        Permission: All authenticated employees
        Returns: Only devices assigned to the requesting user
        """
        user = request.user
        
        # Check if user has employee profile
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        devices = Device.objects.filter(
            employee=user.employee_profile,
            is_active=True
        ).select_related('device_type')
        
        serializer = DeviceListSerializer(devices, many=True)
        return Response({
            "error": 0,
            "data": {
                "count": devices.count(),
                "devices": serializer.data
            }
        })

    @action(detail=False, methods=['get'], url_path='my-history')
    def my_assignment_history(self, request):
        """
        Get device assignment history for logged-in employee
        GET /api/inventory/devices/my-history/
        
        Permission: All authenticated employees
        Returns: Only assignment history for the requesting user
        """
        user = request.user
        
        if not hasattr(user, 'employee_profile'):
            return Response({
                "error": 1,
                "message": "User must have an employee profile"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        assignments = DeviceAssignment.objects.filter(
            employee=user.employee_profile
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

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign device to an employee
        POST /api/inventory/devices/{id}/assign/
        Body: {"employee": 1, "notes": "...", "condition": "good"}
        
        Permission: Admin, Manager, HR only
        """
        device = self.get_object()
        
        if not device.is_active:
            return Response({
                "error": 1,
                "message": "Cannot assign inactive device."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if device.employee:
            return Response({
                "error": 1,
                "message": f"Device is already assigned to {device.employee.get_full_name()}. Please unassign first."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = DeviceAssignSerializer(data=request.data)
        if serializer.is_valid():
            employee = serializer.validated_data['employee']
            notes = serializer.validated_data.get('notes', '')
            condition = serializer.validated_data.get('condition', device.condition)

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
        
        return Response({
            "error": 1,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unassign(self, request, pk=None):
        """
        Unassign device from employee
        POST /api/inventory/devices/{id}/unassign/
        Body: {"notes": "...", "condition": "good"}
        
        Permission: Admin, Manager, HR only
        """
        device = self.get_object()

        if not device.employee:
            return Response({
                "error": 1,
                "message": "Device is not assigned to any employee."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = DeviceUnassignSerializer(data=request.data)
        if serializer.is_valid():
            notes = serializer.validated_data.get('notes', '')
            condition = serializer.validated_data.get('condition', device.condition)
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
        
        return Response({
            "error": 1,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def assignment_history(self, request, pk=None):
        """
        Get assignment history for a specific device
        
        Permission: Admin, Manager, HR only
        """
        device = self.get_object()
        assignments = DeviceAssignment.objects.filter(
            device=device
        ).select_related(
            'employee', 'assigned_by', 'returned_to'
        ).order_by('-assigned_date')
        
        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='unassigned')
    def unassigned_devices(self, request):
        """
        Get all unassigned devices
        
        Permission: Admin, Manager, HR only
        """
        devices = self.get_queryset().filter(
            employee__isnull=True,
            is_active=True,
            status='working'
        )
        serializer = DeviceListSerializer(devices, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='warranty-expiring')
    def warranty_expiring(self, request):
        """
        Get devices with warranty expiring in next 30 days
        
        Permission: Admin, Manager, HR only
        """
        from datetime import timedelta
        
        today = timezone.now().date()
        next_30_days = today + timedelta(days=30)
        
        devices = self.get_queryset().filter(
            warranty_expiry__gte=today,
            warranty_expiry__lte=next_30_days,
            is_active=True
        ).order_by('warranty_expiry')
        
        serializer = DeviceListSerializer(devices, many=True)
        return Response({
            "error": 0,
            "data": {
                "count": devices.count(),
                "devices": serializer.data
            }
        })


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
    
    @action(detail=False, methods=['get'], url_path='recent-assignments')
    def recent_assignments(self, request):
        """Get recent device assignments"""
        limit = int(request.query_params.get('limit', 10))
        
        assignments = DeviceAssignment.objects.select_related(
            'device', 'device__device_type', 'employee', 'assigned_by'
        ).order_by('-assigned_date')[:limit]
        
        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response({
            "error": 0,
            "data": serializer.data
        })

    @action(detail=False, methods=['get'], url_path='audit-status')
    def audit_status(self, request):
        """
        Get status of monthly audits for all assigned devices
        GET /api/inventory/dashboard/audit-status/
        """
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get all assigned devices
        assigned_devices = Device.objects.filter(
            employee__isnull=False,
            is_active=True
        ).select_related('device_type', 'employee')
        
        # Get all audit comments for this month
        audit_comments = DeviceComment.objects.filter(
            created_at__gte=start_of_month,
            comment__startswith='[Monthly Audit]'
        ).values('device_id', 'created_at', 'comment')
        
        # Map device_id to audit info
        audit_map = {a['device_id']: a for a in audit_comments}
        
        results = []
        for device in assigned_devices:
            audit = audit_map.get(device.id)
            results.append({
                'device_id': device.id,
                'serial_number': device.serial_number,
                'device_type': device.device_type.name,
                'employee_name': device.employee.get_full_name(),
                'employee_id': device.employee.employee_id,
                'is_audited': audit is not None,
                'audit_date': audit['created_at'] if audit else None,
                'audit_comment': audit['comment'] if audit else None,
                'current_condition': device.get_condition_display(),
                'current_status': device.get_status_display()
            })
            
        return Response({
            "error": 0,
            "data": {
                "month": now.strftime('%B %Y'),
                "total_assigned": assigned_devices.count(),
                "audited_count": len(audit_map),
                "pending_count": assigned_devices.count() - len(audit_map),
                "details": results
            }
        })

    @action(detail=True, methods=['get'], url_path='user-audit-status')
    def user_audit_status(self, request, pk=None):
        """
        Get audit status of all devices assigned to a specific employee
        GET /api/inventory/dashboard/{employee_id}/user-audit-status/
        """
        # 1. Permission Check
        user = request.user
        target_employee_id = pk
        
        # Check if user is viewing self or is Admin/HR
        is_admin_hr = False
        if user.is_superuser or user.is_staff:
            is_admin_hr = True
        elif hasattr(user, 'employee_profile') and user.employee_profile:
            emp = user.employee_profile
            if emp.designation and emp.designation.level and emp.designation.level <= 3:
                is_admin_hr = True
            
            # If not admin/hr, must match the requested pk
            if not is_admin_hr and str(emp.id) != str(target_employee_id):
                return Response({
                    "error": 1,
                    "message": "You do not have permission to view other employees' audit status."
                }, status=status.HTTP_403_FORBIDDEN)
        
        # 2. Logic
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        devices = Device.objects.filter(
            employee_id=target_employee_id,
            is_active=True
        ).select_related('device_type')
        
        audit_comments = DeviceComment.objects.filter(
            device__in=devices,
            created_at__gte=start_of_month,
            comment__startswith='[Monthly Audit]'
        ).values_list('device_id', flat=True)
        
        audited_device_ids = set(audit_comments)
        
        device_results = []
        all_audited = True
        
        for device in devices:
            is_audited = device.id in audited_device_ids
            if not is_audited:
                all_audited = False
            
            device_results.append({
                "deviceId": device.serial_number or f"DEV_{device.id:03d}",
                "isAudited": is_audited,
                "deviceName": f"{device.brand} {device.model_name}" if device.brand else device.device_type.name
            })
            
        return Response({
            "error": 0,
            "data": {
                "allItemsAudited": all_audited and devices.exists(),
                "devices": device_results
            }
        })
