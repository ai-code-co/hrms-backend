import os
from rest_framework import serializers
from django.db import models, transaction
from .models import Employee, EmergencyContact, Education, WorkHistory, Role, EmployeeDocument
from departments.serializers import DepartmentSerializer, DesignationSerializer


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role"""
    role = serializers.CharField(source='name')
    
    class Meta:
        model = Role
        fields = [
            'id', 'role', 'description',
            'can_view_all_employees', 'can_create_employees',
            'can_edit_all_employees', 'can_delete_employees',
            'can_view_subordinates', 'can_approve_leave',
            'can_approve_timesheet', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer for Emergency Contact"""
    
    class Meta:
        model = EmergencyContact
        fields = [
            'id', 'name', 'relationship', 'phone', 
            'alternate_phone', 'email', 'address', 
            'is_primary', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class EducationSerializer(serializers.ModelSerializer):
    """Serializer for Education"""
    
    class Meta:
        model = Education
        fields = [
            'id', 'level', 'degree', 'field_of_study', 
            'institution', 'start_date', 'end_date', 
            'is_completed', 'percentage', 'grade', 
            'description', 'certificate', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class WorkHistorySerializer(serializers.ModelSerializer):
    """Serializer for Work History"""
    
    class Meta:
        model = WorkHistory
        fields = [
            'id', 'company_name', 'job_title', 'department',
            'start_date', 'end_date', 'is_current', 
            'job_description', 'achievements', 'reason_for_leaving',
            'supervisor_name', 'supervisor_contact', 'salary',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Employee Document"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'document_type', 'document_type_display', 
            'document_url', 'is_verified', 'verified_at', 
            'verified_by', 'created_at', 'updated_at',
            'created_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'verified_at', 'verified_by', 'is_verified']


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
    role_detail = RoleSerializer(source='role', read_only=True)
    department_detail = DepartmentSerializer(source='department', read_only=True)
    designation_detail = DesignationSerializer(source='designation', read_only=True)
    manager_detail = serializers.SerializerMethodField()
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    work_histories = WorkHistorySerializer(many=True, read_only=True)
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    photo_url = serializers.SerializerMethodField()
    are_required_documents_submitted = serializers.BooleanField(read_only=True)
    missing_required_documents = serializers.ListField(child=serializers.CharField(), read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            # Core
            'id', 'employee_id', 'user', 'full_name',
            # Role
            'role', 'role_detail',
            # Personal
            'first_name', 'middle_name', 'last_name', 
            'date_of_birth', 'gender', 'marital_status',
            'nationality', 'blood_group', 'photo', 'photo_url',
            # Contact
            'email', 'phone', 'alternate_phone',
            'address_line1', 'address_line2', 'city',
            'state', 'country', 'postal_code',
            'address_line1_2', 'address_line2_2', 'city_2',
            'state_2', 'country_2', 'postal_code_2',
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
            'emergency_contacts', 'educations', 'work_histories', 'documents',
            'are_required_documents_submitted', 'missing_required_documents',
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

    def get_photo_url(self, obj):
        """Construct full Cloudinary URL from stored photo path/public_id"""
        if not obj.photo:
            return None
        
        if obj.photo.startswith('http'):
            return obj.photo
            
        cloudinary_base = os.getenv('CLOUDINARY_BASE_URL', 'https://res.cloudinary.com/dhlyvqdoi/image/upload')
        return f"{cloudinary_base}/{obj.photo}"



class EmployeeLookupSerializer(serializers.ModelSerializer):
    """Lightweight serializer for employee selection lists"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 
            'designation_name', 'photo', 'photo_url'
        ]

    def get_photo_url(self, obj):
        """Construct full Cloudinary URL from stored photo path/public_id"""
        if not obj.photo:
            return None
        
        if obj.photo.startswith('http'):
            return obj.photo
            
        import os
        cloudinary_base = os.getenv('CLOUDINARY_BASE_URL', 'https://res.cloudinary.com/dhlyvqdoi/image/upload')
        return f"{cloudinary_base}/{obj.photo}"


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employees"""
    
    emergency_contacts = EmergencyContactSerializer(many=True, required=False)
    educations = EducationSerializer(many=True, required=False)
    work_histories = WorkHistorySerializer(many=True, required=False)
    documents = EmployeeDocumentSerializer(many=True, required=False)

    class Meta:
        model = Employee
        fields = [
            'user', 'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender', 'marital_status',
            'nationality', 'blood_group', 'photo',
            'email', 'phone', 'alternate_phone',
            'address_line1', 'address_line2', 'city',
            'state', 'country', 'postal_code',
            'address_line1_2', 'address_line2_2', 'city_2',
            'state_2', 'country_2', 'postal_code_2',
            'role', 'department', 'designation', 'reporting_manager',
            'employee_type', 'employment_status', 'joining_date',
            'probation_end_date', 'confirmation_date', 'work_location',
            'pan_number', 'aadhar_number', 'passport_number',
            'driving_license', 'bank_name', 'account_number',
            'ifsc_code', 'account_holder_name', 'is_active',
            'emergency_contacts', 'educations', 'work_histories', 'documents'
        ]
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if self.instance and self.instance.email == value:
            return value
        if Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError("An employee with this email already exists.")
        return value
    
    def validate_pan_number(self, value):
        """Validate PAN format: ABCDE1234F"""
        if value:
            import re
            value = value.upper().strip()
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', value):
                raise serializers.ValidationError("PAN must be in format: ABCDE1234F (e.g., ABCDE1234F)")
        return value
    
    def validate_aadhar_number(self, value):
        """Validate Aadhaar format: 12 digits"""
        if value:
            value = value.strip().replace(' ', '').replace('-', '')
            if not value.isdigit() or len(value) != 12:
                raise serializers.ValidationError("Aadhaar must be exactly 12 digits")
        return value
    
    def validate_ifsc_code(self, value):
        """Validate IFSC format: ABCD0123456"""
        if value:
            import re
            value = value.upper().strip()
            if not re.match(r'^[A-Z]{4}0[0-9A-Z]{6}$', value):
                raise serializers.ValidationError("IFSC must be in format: ABCD0123456 (e.g., HDFC0001234)")
        return value
    
    def validate_reporting_manager(self, value):
        """Prevent circular manager references"""
        if value:
            employee = self.instance
            if employee and value.id == employee.id:
                raise serializers.ValidationError(
                    "An employee cannot be their own manager."
                )
            
            # Check for circular references (manager's manager chain)
            if employee:
                current = value
                visited = set()
                max_depth = 10  # Prevent infinite loops
                depth = 0
                
                while current and current.reporting_manager and depth < max_depth:
                    if current.id == employee.id:
                        raise serializers.ValidationError(
                            "Circular manager reference detected. This would create a loop in the management hierarchy."
                        )
                    if current.id in visited:
                        break  # Already checked this chain
                    visited.add(current.id)
                    current = current.reporting_manager
                    depth += 1
        
        return value
    
    def validate_role(self, value):
        """Validate role assignment permissions"""
        request = self.context.get('request')
        if not request:
            return value
        
        user = request.user
        
        # Superuser can assign any role
        if user.is_superuser:
            return value
        
        # Check if user has permission to assign roles
        if hasattr(user, 'employee_profile') and user.employee_profile.role:
            # Only Admin/HR can assign roles
            if not user.employee_profile.role.can_create_employees:
                raise serializers.ValidationError(
                    "You do not have permission to assign roles. Only Admin/HR can assign roles."
                )
        elif not user.is_staff:
            # Non-staff users without employee profile cannot assign roles
            raise serializers.ValidationError(
                "You do not have permission to assign roles."
            )
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Get values from data or existing instance
        joining_date = data.get('joining_date') or (self.instance.joining_date if self.instance else None)
        probation_end_date = data.get('probation_end_date') or (self.instance.probation_end_date if self.instance else None)
        confirmation_date = data.get('confirmation_date') or (self.instance.confirmation_date if self.instance else None)
        department = data.get('department') or (self.instance.department if self.instance else None)
        designation = data.get('designation') or (self.instance.designation if self.instance else None)
        
        # Date validation
        if joining_date and probation_end_date:
            if probation_end_date < joining_date:
                raise serializers.ValidationError({
                    'probation_end_date': 'Probation end date must be after joining date.'
                })
        
        if probation_end_date and confirmation_date:
            if confirmation_date < probation_end_date:
                raise serializers.ValidationError({
                    'confirmation_date': 'Confirmation date must be after probation end date.'
                })
        
        # Department and designation consistency check
        if department and designation:
            if designation.department != department:
                raise serializers.ValidationError({
                    'designation': 'Designation must belong to the selected department.'
                })
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Handle nested creation of emergency contacts, educations, and work history"""
        emergency_contacts_data = validated_data.pop('emergency_contacts', [])
        educations_data = validated_data.pop('educations', [])
        work_histories_data = validated_data.pop('work_histories', [])
        documents_data = validated_data.pop('documents', [])
        
        # System fields passed from perform_create
        created_by = validated_data.get('created_by')
        updated_by = validated_data.get('updated_by')
        
        employee = Employee.objects.create(**validated_data)
        
        # Create emergency contacts
        for contact_data in emergency_contacts_data:
            EmergencyContact.objects.create(
                employee=employee,
                created_by=created_by,
                updated_by=updated_by,
                **contact_data
            )
            
        # Create education records
        for education_data in educations_data:
            Education.objects.create(
                employee=employee,
                created_by=created_by,
                updated_by=updated_by,
                **education_data
            )
            
        # Create work history records
        for history_data in work_histories_data:
            WorkHistory.objects.create(
                employee=employee,
                created_by=created_by,
                updated_by=updated_by,
                **history_data
            )
            
        # Create documents
        for document_data in documents_data:
            EmployeeDocument.objects.create(
                employee=employee,
                created_by=created_by,
                **document_data
            )
            
        return employee

    @transaction.atomic
    def update(self, instance, validated_data):
        """Handle nested updates for emergency contacts, educations, and work history"""
        emergency_contacts_data = validated_data.pop('emergency_contacts', None)
        educations_data = validated_data.pop('educations', None)
        work_histories_data = validated_data.pop('work_histories', None)
        documents_data = validated_data.pop('documents', None)
        
        # System field passed from perform_update
        updated_by = validated_data.get('updated_by')
        
        # Update main employee fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update emergency contacts (replace existing with new list)
        if emergency_contacts_data is not None:
            instance.emergency_contacts.all().delete()
            for contact_data in emergency_contacts_data:
                EmergencyContact.objects.create(
                    employee=instance,
                    updated_by=updated_by,
                    created_by=instance.created_by, # Keep original creator
                    **contact_data
                )
                
        # Update education records
        if educations_data is not None:
            instance.educations.all().delete()
            for education_data in educations_data:
                Education.objects.create(
                    employee=instance,
                    updated_by=updated_by,
                    created_by=instance.created_by,
                    **education_data
                )
                
        # Update work history
        if work_histories_data is not None:
            instance.work_histories.all().delete()
            for history_data in work_histories_data:
                WorkHistory.objects.create(
                    employee=instance,
                    updated_by=updated_by,
                    created_by=instance.created_by,
                    **history_data
                )
        
        # Update documents
        if documents_data is not None:
            # We don't necessarily want to delete all documents, 
            # but for consistency with others, we'll replace the provided types
            for doc_data in documents_data:
                EmployeeDocument.objects.update_or_create(
                    employee=instance,
                    document_type=doc_data.get('document_type'),
                    defaults={
                        'document_url': doc_data.get('document_url'),
                        'created_by': instance.created_by if not instance.documents.filter(document_type=doc_data.get('document_type')).exists() else None
                    }
                )
                
        return instance


class EmployeeAdminDetailSerializer(EmployeeDetailSerializer):
    """
    HR/Admin → full employee data
    """
    class Meta(EmployeeDetailSerializer.Meta):
        fields = EmployeeDetailSerializer.Meta.fields


class EmployeeSelfDetailSerializer(EmployeeDetailSerializer):
    """
    Employee → own profile (NO sensitive data)
    Excludes redundant ID fields when detailed objects are present
    """
    class Meta(EmployeeDetailSerializer.Meta):
        fields = None
        exclude = [
            # Sensitive identity documents
            "pan_number",
            "aadhar_number",
            "passport_number",
            "driving_license",
            # Redundant ID fields (we have _detail versions)
            "department",
            "designation",
            "reporting_manager",
            # System/internal fields
            "company",
            "user",
            "created_by",
            "updated_by",
        ]


class EmployeeManagerDetailSerializer(EmployeeDetailSerializer):
    """
    Manager → reportees (very limited data)
    """
    class Meta(EmployeeDetailSerializer.Meta):
        fields = None
        exclude = [
            # Identity
            "pan_number",
            "aadhar_number",
            "passport_number",
            "driving_license",

            # Financial
            "bank_name",
            "account_number",
            "ifsc_code",
            "account_holder_name",

        ]
