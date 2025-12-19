from rest_framework import serializers
from .models import DeviceType, Device, DeviceAssignment
from employees.serializers import EmployeeListSerializer
from employees.models import Employee


class DeviceTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for device type lists"""
    total = serializers.IntegerField(source='total_devices', read_only=True)
    working = serializers.IntegerField(source='working_devices', read_only=True)
    unassigned = serializers.IntegerField(source='unassigned_devices', read_only=True)

    class Meta:
        model = DeviceType
        fields = ['id', 'name', 'description', 'is_active', 'total', 'working', 'unassigned', 'created_at']


class DeviceTypeSerializer(serializers.ModelSerializer):
    """Detailed serializer for device type"""
    total = serializers.IntegerField(source='total_devices', read_only=True)
    working = serializers.IntegerField(source='working_devices', read_only=True)
    unassigned = serializers.IntegerField(source='unassigned_devices', read_only=True)

    class Meta:
        model = DeviceType
        fields = [
            'id', 'name', 'description', 'is_active',
            'total', 'working', 'unassigned',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DeviceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for device lists"""
    device_type_name = serializers.CharField(source='device_type.name', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.IntegerField(source='employee.id', read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'device_type', 'device_type_name', 'serial_number',
            'status', 'employee', 'employee_id', 'employee_name',
            'purchase_date', 'is_active', 'created_at'
        ]


class DeviceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for device"""
    device_type_detail = DeviceTypeSerializer(source='device_type', read_only=True)
    employee_detail = EmployeeListSerializer(source='employee', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    assignment_history = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            'id', 'device_type', 'device_type_detail', 'serial_number',
            'status', 'employee', 'employee_detail',
            'purchase_date', 'purchase_price', 'warranty_expiry',
            'notes', 'is_active',
            'created_at', 'updated_at',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'assignment_history'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'assignment_history'
        ]

    def get_assignment_history(self, obj):
        """Get assignment history for the device"""
        assignments = obj.assignment_history.all()[:10]  # Last 10 assignments
        return DeviceAssignmentSerializer(assignments, many=True).data


class DeviceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating devices"""

    class Meta:
        model = Device
        fields = [
            'device_type', 'serial_number', 'status', 'employee',
            'purchase_date', 'purchase_price', 'warranty_expiry',
            'notes', 'is_active'
        ]

    def validate_serial_number(self, value):
        """Validate serial number uniqueness"""
        if value:
            queryset = Device.objects.filter(serial_number=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("A device with this serial number already exists.")
        return value


class DeviceAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for device assignments"""
    device_info = serializers.CharField(source='device.__str__', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)

    class Meta:
        model = DeviceAssignment
        fields = [
            'id', 'device', 'device_info', 'employee', 'employee_name',
            'assigned_by', 'assigned_by_name', 'assigned_date',
            'returned_date', 'notes'
        ]
        read_only_fields = ['assigned_date', 'assigned_by']


class DeviceAssignSerializer(serializers.Serializer):
    """Serializer for assigning a device to an employee"""
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_active=True),
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_employee(self, value):
        """Validate employee is active (additional safety check)"""
        if not value.is_active:
            raise serializers.ValidationError("Cannot assign device to inactive employee.")
        return value


class DeviceUnassignSerializer(serializers.Serializer):
    """Serializer for unassigning a device from an employee"""
    notes = serializers.CharField(required=False, allow_blank=True)

