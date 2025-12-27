from rest_framework import serializers
from .models import DeviceType, Device, DeviceAssignment
from employees.models import Employee


class DeviceTypeDropdownSerializer(serializers.ModelSerializer):
    """Minimal serializer for device type dropdowns"""
    class Meta:
        model = DeviceType
        fields = ['id', 'name']


class DeviceTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for device type lists"""
    total = serializers.IntegerField(source='total_devices', read_only=True)
    working = serializers.IntegerField(source='working_devices', read_only=True)
    unassigned = serializers.IntegerField(source='unassigned_devices', read_only=True)
    assigned = serializers.IntegerField(source='assigned_devices', read_only=True)

    class Meta:
        model = DeviceType
        fields = [
            'id', 'name', 'description', 'icon',
            'is_assignable', 'requires_serial_number', 'is_active', 
            'total', 'working', 'unassigned', 'assigned', 
            'created_at'
        ]


class DeviceTypeSerializer(serializers.ModelSerializer):
    """Detailed serializer for device type"""
    total = serializers.IntegerField(source='total_devices', read_only=True)
    working = serializers.IntegerField(source='working_devices', read_only=True)
    unassigned = serializers.IntegerField(source='unassigned_devices', read_only=True)
    assigned = serializers.IntegerField(source='assigned_devices', read_only=True)

    class Meta:
        model = DeviceType
        fields = [
            'id', 'name', 'description', 'icon',
            'default_warranty_months', 'requires_serial_number',
            'is_assignable', 'is_active',
            'total', 'working', 'unassigned', 'assigned',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DeviceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for device lists"""
    device_type_name = serializers.CharField(source='device_type.name', read_only=True)
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.IntegerField(source='employee.id', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    is_under_warranty = serializers.BooleanField(read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'device_type', 'device_type_name', 
            'serial_number', 'internal_serial_number', 'model_name', 'brand',
            'status', 'status_display', 
            'condition', 'condition_display',
            'employee', 'employee_id', 'employee_name',
            'purchase_date', 'warranty_expiry', 'is_under_warranty',
            'invoice_image', 'device_image',
            'is_active', 'created_at'
        ]
    
    def get_employee_name(self, obj):
        if obj.employee:
            return obj.employee.get_full_name()
        return None


class DeviceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for device"""
    device_type_detail = DeviceTypeSerializer(source='device_type', read_only=True)
    employee_detail = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    assignment_history = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    is_under_warranty = serializers.BooleanField(read_only=True)
    is_assigned = serializers.BooleanField(read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'device_type', 'device_type_detail', 
            'serial_number', 'internal_serial_number', 'model_name', 'brand',
            'status', 'status_display',
            'condition', 'condition_display',
            'employee', 'employee_detail',
            'purchase_date', 'purchase_price', 
            'warranty_expiry', 'is_under_warranty',
            'invoice_image', 'device_image',
            'notes', 'is_active', 'is_assigned',
            'created_at', 'updated_at',
            'created_by', 'created_by_name', 
            'updated_by', 'updated_by_name',
            'assignment_history'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'assignment_history'
        ]

    def get_employee_detail(self, obj):
        """Get employee details if assigned"""
        if not obj.employee:
            return None
        return {
            'id': obj.employee.id,
            'employee_id': obj.employee.employee_id,
            'full_name': obj.employee.get_full_name(),
            'email': obj.employee.email,
            'department': obj.employee.department.name if obj.employee.department else None,
            'designation': obj.employee.designation.name if obj.employee.designation else None,
        }

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None

    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.email
        return None

    def get_assignment_history(self, obj):
        """Get assignment history for the device"""
        assignments = obj.assignment_history.all()[:10]
        return DeviceAssignmentSerializer(assignments, many=True).data


class DeviceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating devices"""
    
    serial_number = serializers.CharField(required=True)
    internal_serial_number = serializers.CharField(required=True)
    purchase_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    class Meta:
        model = Device
        fields = [
            'device_type', 'serial_number', 'internal_serial_number', 'model_name', 'brand',
            'status', 'condition', 'employee',
            'purchase_date', 'purchase_price', 'warranty_expiry',
            'invoice_image', 'device_image',
            'notes', 'is_active'
        ]

    def validate_serial_number(self, value):
        """Validate serial number uniqueness"""
        if not value:
            raise serializers.ValidationError("Serial number is required.")
        queryset = Device.objects.filter(serial_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "A device with this serial number already exists."
            )
        return value
    
    def validate_internal_serial_number(self, value):
        """Validate internal serial number uniqueness"""
        if not value:
            raise serializers.ValidationError("Internal serial number is required.")
        queryset = Device.objects.filter(internal_serial_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "A device with this internal serial number already exists."
            )
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        purchase_date = data.get('purchase_date')
        warranty_expiry = data.get('warranty_expiry')
        
        if purchase_date and warranty_expiry:
            if warranty_expiry < purchase_date:
                raise serializers.ValidationError({
                    'warranty_expiry': 'Warranty expiry cannot be before purchase date.'
                })
        
        return data


class DeviceAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for device assignments"""
    device_info = serializers.SerializerMethodField()
    device_type = serializers.CharField(source='device.device_type.name', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_str = serializers.CharField(source='employee.employee_id', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    returned_to_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeviceAssignment
        fields = [
            'id', 'device', 'device_info', 'device_type',
            'employee', 'employee_name', 'employee_id_str',
            'assigned_by', 'assigned_by_name', 'assigned_date',
            'returned_date', 'returned_to', 'returned_to_name',
            'condition_at_assignment', 'condition_at_return',
            'notes', 'is_active', 'duration_days'
        ]
        read_only_fields = ['assigned_date', 'assigned_by']
    
    def get_device_info(self, obj):
        return str(obj.device)
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return obj.assigned_by.get_full_name() or obj.assigned_by.email
        return None
    
    def get_returned_to_name(self, obj):
        if obj.returned_to:
            return obj.returned_to.get_full_name() or obj.returned_to.email
        return None


class DeviceAssignmentActionSerializer(serializers.Serializer):
    """
    Unified serializer for assigning/unassigning a device
    
    - To assign: Provide 'employee' field
    - To unassign: Omit 'employee' field or set to null
    """
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="Employee ID to assign the device to. Omit or set to null to unassign."
    )
    notes = serializers.CharField(
        required=False, 
        allow_blank=True, 
        max_length=500,
        help_text="Notes about the assignment/unassignment"
    )
    condition = serializers.ChoiceField(
        choices=Device.CONDITION_CHOICES,
        required=False,
        help_text="Device condition at assignment/return"
    )

    def validate_employee(self, value):
        """Validate employee is active if provided"""
        if value and not value.is_active:
            raise serializers.ValidationError(
                "Cannot assign device to inactive employee."
            )
        return value
