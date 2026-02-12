from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Count, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser
import cloudinary
import cloudinary.uploader
import os
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


from employees.permissions import IsAdminOrManagerOrOwner
from employees.filters import HierarchyFilterBackend

class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Device management
    
    Permissions:
    - List/Retrieve all devices: Admin, Manager (subordinates), HR only
    - Create/Update/Delete: Admin, Manager, HR only
    - Assign/Unassign: Admin, Manager, HR only
    - My Devices/My History: All authenticated employees (own devices only)
    """
    queryset = Device.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrManagerOrOwner]
    filter_backends = [HierarchyFilterBackend, SearchFilter, OrderingFilter]
    
    
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
        """Queryset is filtered by HierarchyFilterBackend"""
        return super().get_queryset().select_related(
            'device_type', 'employee', 'created_by', 'updated_by'
        )

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
        if self.action in ['assignment_history', 'unassigned_devices', 'warranty_expiring', 'comments']:
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
        """Hard delete device"""
        # instance.is_active = False
        # instance.updated_by = self.request.user
        # instance.save()
        
        # hard delete
        instance.delete()

    # ═══════════════════════════════════════════════════════════
    # EMPLOYEE SELF-SERVICE ENDPOINTS (All authenticated users)
    # ═══════════════════════════════════════════════════════════

    @action(detail=False,methods=['post'],url_path='bulk-add')
    def bulk_add_device(self,request,pk=None):
        """
        To add multiple devices
        
        POST /api/inventory/devices/bulk-add
        """
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Send a JSON array of Inventory."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # device = self.get_object()
        user = request.user
        
        serializer = DeviceListSerializer(data=request.data,many=True)
        serializer.is_valid(raise_exception=True)
        
        created =[]
        
        for item in serializer.validated_data:
            obj = Device.objects.create(
                **item,
                created_by=user,
                updated_by=user
            )
            created.append(obj)
        return Response(
            DeviceListSerializer(created,many=True).data,
            status=status.HTTP_201_CREATED
        )     

    @swagger_auto_schema(
        operation_description="Submit a monthly inventory audit for an assigned device.",
        request_body=DeviceSubmitAuditSerializer,
        responses={
            201: openapi.Response(
                description="Audit submitted successfully",
                examples={
                    "application/json": {
                        "error": 0,
                        "message": "Monthly audit submitted successfully. Device status updated.",
                        "data": {
                            "audit_id": 1,
                            "condition": "Excellent",
                            "status": "Working"
                        }
                    }
                }
            ),
            400: "Validation failed or duplicate audit",
            403: "Permission denied"
        }
    )
    @action(detail=True, methods=['post'], url_path='submit-audit')
    def submit_audit(self, request, pk=None):
        """
        Submit a monthly inventory audit for an assigned device.
        POST /api/inventory/devices/{id}/submit-audit/
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
        comment_type = serializer.validated_data.get('comment_type', 'all_good')
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
            comment_type=comment_type,
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

    @action(detail=True, methods=['post'], url_path='upload-document',parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        device = self.get_object()
        file_obj = request.FILES.get('file')
        doc_type = request.data.get('doc_type')  # photo / warranty_doc / invoice_doc

        if not file_obj:
            return Response({"error": 1, "message": "No file provided"}, status=400)

        if doc_type not in ['photo', 'warranty_doc', 'invoice_doc']:
            return Response({"error": 1, "message": "Invalid doc_type"}, status=400)

        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        )

        resource_type = "image" if (file_obj.content_type or "").startswith("image/") else "raw"
        uploaded = cloudinary.uploader.upload(
            file_obj,
            folder=f"hrms/devices/{device.id}",
            resource_type=resource_type,
            original_filename=True
        )

        file_url = uploaded.get("secure_url")
        if not file_url:
            return Response({"error": 1, "message": "Upload failed"}, status=500)

        # updates Device table field: photo / warranty_doc / invoice_doc
        setattr(device, doc_type, file_url)
        device.updated_by = request.user
        device.save(update_fields=[doc_type, "updated_by", "updated_at"])

        # sync only photo to EmployeeDocument 
        # if device.employee and doc_type == "photo":
        #     EmployeeDocument.objects.update_or_create(
        #         employee=device.employee,
        #         document_type="photo",
        #         defaults={"document_url": file_url, "created_by": request.user}
        #     )

        return Response({
            "error": 0,
            "message": "Document uploaded successfully",
            "data": {
                "device_id": device.id,
                "doc_type": doc_type,
                "url": file_url,
                "public_id": uploaded.get("public_id")
            }
        }, status=200)

    
    @action(detail=True, methods=['delete'], url_path='delete-document')
    def delete_document(self, request, pk=None):
        device = self.get_object()
        doc_type = request.data.get('doc_type')
        public_id = request.data.get('doc_type')
        
        if doc_type not in ['photo', 'warranty_doc', 'invoice_doc']:
            return Response({"error": 1, "message": "Invalid doc_type"}, status=400)
        
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        )
        
        result = cloudinary.uploader.destroy(
            f"hrms/documents/{public_id}",
            resource_type="image",
            invalidate=True
        )
        
        if result.get("result") not in ["ok", "not found"]:
            return Response({
                "error":1,
                "message":"Failed to delete the image/file in cloudinary"
                }, status=400)
        
        setattr(device, doc_type, None)
        device.updated_by = request.user
        device.save(update_fields=[doc_type, "updated_by", "updated_at"])
        
        return Response({
            "error": 0,
            "message": "Document uploaded successfully",
            "data": {
                "device_id": device.id,
                "doc_type": doc_type,
            }
        }, status=200)
       
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
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """
        Get all comments/history for a device
        GET /api/inventory/devices/{id}/comments/
        """
        device = self.get_object()
        comments = device.comments.all().select_related('employee').order_by('-created_at')
        serializer = DeviceCommentSerializer(comments, many=True)
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
        GET /api/inventory/summary/
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

    @swagger_auto_schema(
        operation_description="Get summary of monthly audits for all assigned devices (HR/Admin view).",
        responses={200: "Success"}
    )
    @action(detail=False, methods=['get'], url_path='audit-summary')
    def audit_summary(self, request):
        """
        Get summary of monthly audits for all assigned devices
        GET /api/inventory/audit-summary/?month=1&year=2026
        """
        import datetime
        from django.db.models import Max
        
        # 1. Parse Month/Year
        now = timezone.now()
        try:
            month = int(request.query_params.get('month', now.month))
            year = int(request.query_params.get('year', now.year))
            start_date = datetime.datetime(year, month, 1)
            if month == 12:
                end_date = datetime.datetime(year + 1, 1, 1)
            else:
                end_date = datetime.datetime(year, month + 1, 1)
            
            # Make timezone aware
            start_date = timezone.make_aware(start_date)
            end_date = timezone.make_aware(end_date)
        except (ValueError, TypeError):
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + datetime.timedelta(days=32)).replace(day=1)
            month = start_date.month
            year = start_date.year

        # 2. Base Querysets
        all_active_devices = Device.objects.filter(is_active=True).select_related('device_type', 'employee')
        
        # 3. Get Audits for the selected month
        # We only care about the LATEST audit for a device in that month
        # Since MySQL/TiDB doesn't support .distinct('field'), we filter in Python
        all_audits = DeviceComment.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            comment__startswith='[Monthly Audit]'
        ).order_by('-created_at').select_related('employee')
        
        audit_map = {}
        for a in all_audits:
            if a.device_id not in audit_map:
                audit_map[a.device_id] = a
        
        # 4. Calculate Stats
        total_inventories = all_active_devices.count()
        unassigned_inventories = all_active_devices.filter(employee__isnull=True).count()
        assigned_devices = all_active_devices.filter(employee__isnull=False)
        
        audit_done_count = len(audit_map)
        audit_pending_count = max(0, assigned_devices.count() - audit_done_count)
        
        # Breakdown of audit types
        audit_good = 0
        audit_issue = 0
        audit_critical_issue = 0
        
        for audit in audit_map.values():
            if audit.comment_type == 'all_good':
                audit_good += 1
            elif audit.comment_type == 'issue':
                audit_issue += 1
            elif audit.comment_type == 'critical_issue':
                audit_critical_issue += 1
            else:
                # Default to good if not specified
                audit_good += 1

        # 5. Build Audit List
        audit_list = []
        for device in all_active_devices:
            audit = audit_map.get(device.id)
            
            # Map fields to match USER requested format
            audit_list.append({
                "id": str(device.id),
                "machine_type": device.device_type.name,
                "machine_name": device.brand or device.model_name or "Unknown",
                "serial_number": device.serial_number or "",
                "bill_number": device.notes[:20] if device.notes else "", # Placeholder mapping
                "machine_id": str(device.id),
                "assigned_user_id": str(device.employee.id) if device.employee else None,
                "file_name": device.photo if device.photo else None,
                "audit_id": str(audit.id) if audit else None,
                "inventory_id": str(device.id),
                "month": str(month),
                "year": str(year),
                "audit_done_by_user_id": str(audit.employee.id) if audit and audit.employee else None,
                "comment_type": audit.comment_type if audit else None,
                "comment": audit.comment.replace('[Monthly Audit] ', '') if audit else None,
                "audit_done_by": audit.employee.get_full_name() if audit and audit.employee else None,
                "assigned_to": device.employee.get_full_name() if device.employee else None,
            })
        employee_map = {}
        for item in audit_list:
            emp_name = item["assigned_to"] or "Unassigned"
            if emp_name not in employee_map:
                employee_map[emp_name] = []
            employee_map[emp_name].append(item)
            
        audit_list_employee_wise = []
        for emp_name, items in employee_map.items():
            audit_list_employee_wise.append({
                "employee_name": emp_name,
                "items": items
            })

        return Response({
            "error": 0,
            "message": "Inventory Audit List",
            "data": {
                "stats": {
                    "total_inventories": total_inventories,
                    "audit_done": audit_done_count,
                    "audit_pending": audit_pending_count,
                    "unassigned_inventories": unassigned_inventories,
                    "audit_good": audit_good,
                    "audit_issue": audit_issue,
                    "audit_critical_issue": audit_critical_issue
                },
                "audit_list": audit_list,
                "audit_list_employee_wise": audit_list_employee_wise
            }
        })

    @action(detail=False, methods=['get'], url_path='audit-history')
    def audit_history(self, request):
        """
        Get historical audit performance for the last 6 months
        GET /api/inventory/audit-history/
        """
        import datetime
        now = timezone.now()
        history = []
        
        for i in range(6):
            # Calculate month and year
            month_idx = now.month - i
            year_idx = now.year
            while month_idx <= 0:
                month_idx += 12
                year_idx -= 1
            
            start_date = timezone.make_aware(datetime.datetime(year_idx, month_idx, 1))
            if month_idx == 12:
                next_month = 1
                next_year = year_idx + 1
            else:
                next_month = month_idx + 1
                next_year = year_idx
            
            end_date = timezone.make_aware(datetime.datetime(next_year, next_month, 1))
            
            # Count active assignments during this period
            assigned_count = DeviceAssignment.objects.filter(
                Q(assigned_date__lt=end_date) & 
                (Q(returned_date__isnull=True) | Q(returned_date__gt=start_date))
            ).values('device_id').distinct().count()
            
            # Count audits done in this month
            audit_count = DeviceComment.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                comment__startswith='[Monthly Audit]'
            ).values('device_id').distinct().count()
            
            history.append({
                "month": start_date.strftime("%B"),
                "year": str(year_idx),
                "total_assigned": assigned_count,
                "audited_count": audit_count,
                "pending_count": max(0, assigned_count - audit_count),
                "completion_rate": round((audit_count / assigned_count * 100), 1) if assigned_count > 0 else 0
            })
            
        return Response({
            "error": 0,
            "message": "Audit History (Last 6 Months)",
            "data": history[::-1] # Chronological order
        })

    @swagger_auto_schema(
        operation_description="Get audit status of all devices assigned to a specific employee.",
        manual_parameters=[
            openapi.Parameter(
                'employee_id', openapi.IN_QUERY, 
                description="ID of the employee (optional if viewing self)", 
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="Success",
                examples={
                    "application/json": {
                        "error": 0,
                        "data": {
                            "allItemsAudited": True,
                            "devices": [
                                {
                                    "id": 1,
                                    "serial_number": "SN123",
                                    "isAudited": True,
                                    "device_type_name": "Laptop"
                                }
                            ]
                        }
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='user-audit-status')
    def user_audit_status(self, request):
        """
        Get audit status of all devices assigned to a specific employee
        GET /api/inventory/user-audit-status/?employee_id=123 (Optional for Admin)
        """
        # 1. Permission Check
        user = request.user
        
        # Determine target employee (from query param or self)
        target_employee_id = request.query_params.get('employee_id')
        
        if not target_employee_id:
            if hasattr(user, 'employee_profile') and user.employee_profile:
                target_employee_id = user.employee_profile.id
            else:
                return Response({
                    "error": 1,
                    "message": "employee_id is required or user must have an employee profile."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is viewing self or is Admin/HR
        is_admin_hr = False
        if user.is_superuser or user.is_staff:
            is_admin_hr = True
        elif hasattr(user, 'employee_profile') and user.employee_profile:
            emp = user.employee_profile
            if emp.designation and emp.designation.level and emp.designation.level <= 3:
                is_admin_hr = True
            
            # If not admin/hr, must match the requested target_employee_id
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
        
        all_audited = devices.exists()
        device_results = []
        
        for device in devices:
            is_audited = device.id in audited_device_ids
            device_results.append({
                "id": device.id,
                "serial_number": device.serial_number,
                "isAudited": is_audited,
            })
            if not is_audited:
                all_audited = False
            
        return Response({
            "error": 0,
            "data": {
                "allItemsAudited": all_audited,
                "devices": device_results
            }
        })