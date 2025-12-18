from rest_framework import serializers
from .models import Employee, EmergencyContact, Education, WorkHistory
from departments.serializers import DepartmentSerializer, DesignationSerializer


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer for Emergency Contact"""
    
    class Meta:
        model = EmergencyContact
        fields = [
            'id', 'name', 'relationship', 'phone', 
            'alternate_phone', 'email', 'address', 
            'is_primary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EducationSerializer(serializers.ModelSerializer):
    """Serializer for Education"""
    
    class Meta:
        model = Education
        fields = [
            'id', 'level', 'degree', 'field_of_study', 
            'institution', 'start_date', 'end_date', 
            'is_completed', 'percentage', 'grade', 
            'description', 'certificate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WorkHistorySerializer(serializers.ModelSerializer):
    """Serializer for Work History"""
    
    class Meta:
        model = WorkHistory
        fields = [
            'id', 'company_name', 'job_title', 'department',
            'start_date', 'end_date', 'is_current', 
            'job_description', 'achievements', 'reason_for_leaving',
            'supervisor_name', 'supervisor_contact', 'salary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for employee lists"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    manager_name = serializers.CharField(source='reporting_manager.get_full_name', read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'email', 'phone',
            'department', 'department_name', 'designation', 
            'designation_name', 'reporting_manager', 'manager_name',
            'employment_status', 'employee_type', 'joining_date',
            'photo', 'is_active'
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for employee with related data"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    department_detail = DepartmentSerializer(source='department', read_only=True)
    designation_detail = DesignationSerializer(source='designation', read_only=True)
    manager_detail = serializers.SerializerMethodField()
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    work_histories = WorkHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            # Core
            'id', 'employee_id', 'user', 'full_name',
            # Personal
            'first_name', 'middle_name', 'last_name', 
            'date_of_birth', 'gender', 'marital_status',
            'nationality', 'blood_group', 'photo',
            # Contact
            'email', 'phone', 'alternate_phone',
            'address_line1', 'address_line2', 'city',
            'state', 'country', 'postal_code',
            # Professional
            'department', 'department_detail', 'designation', 
            'designation_detail', 'reporting_manager', 'manager_detail',
            'employee_type', 'employment_status', 'joining_date',
            'probation_end_date', 'confirmation_date', 'work_location',
            # Documents
            'pan_number', 'aadhar_number', 'passport_number', 
            'driving_license',
            # Financial
            'bank_name', 'account_number', 'ifsc_code', 
            'account_holder_name',
            # Related Data
            'emergency_contacts', 'educations', 'work_histories',
            # System
            'is_active', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = [
            'employee_id', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
    
    def get_manager_detail(self, obj):
        """Get manager details if exists"""
        if obj.reporting_manager:
            return {
                'id': obj.reporting_manager.id,
                'employee_id': obj.reporting_manager.employee_id,
                'full_name': obj.reporting_manager.get_full_name(),
                'email': obj.reporting_manager.email,
                'designation': obj.reporting_manager.designation.name if obj.reporting_manager.designation else None
            }
        return None


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employees"""
    
    class Meta:
        model = Employee
        fields = [
            'user', 'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender', 'marital_status',
            'nationality', 'blood_group', 'photo',
            'email', 'phone', 'alternate_phone',
            'address_line1', 'address_line2', 'city',
            'state', 'country', 'postal_code',
            'department', 'designation', 'reporting_manager',
            'employee_type', 'employment_status', 'joining_date',
            'probation_end_date', 'confirmation_date', 'work_location',
            'pan_number', 'aadhar_number', 'passport_number',
            'driving_license', 'bank_name', 'account_number',
            'ifsc_code', 'account_holder_name', 'is_active'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if self.instance and self.instance.email == value:
            return value
        if Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError("An employee with this email already exists.")
        return value

