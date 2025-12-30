from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms
from .models import Employee, EmergencyContact, Education, WorkHistory, Role
from auth_app.models import User


class EmployeeAdminForm(forms.ModelForm):
    """Custom form to validate user selection"""
    
    class Meta:
        model = Employee
        fields = '__all__'
    
    def clean_user(self):
        """Ensure only verified users can be linked to employees"""
        user = self.cleaned_data.get('user')
        if user:
            if not user.is_verified:
                raise ValidationError(
                    "Only verified users can be linked to employees. "
                    "Please verify the user first before creating an employee record."
                )
            # Check if user already has an employee profile
            if hasattr(user, 'employee_profile') and self.instance.pk != user.employee_profile.pk:
                raise ValidationError(
                    f"This user ({user.username}) is already linked to another employee."
                )
        return user


class EmergencyContactInline(admin.TabularInline):
    """Inline admin for Emergency Contacts"""
    model = EmergencyContact
    extra = 1
    fields = ('name', 'relationship', 'phone', 'alternate_phone', 'email', 'is_primary')


class EducationInline(admin.TabularInline):
    """Inline admin for Education"""
    model = Education
    extra = 1
    fields = ('level', 'degree', 'field_of_study', 'institution', 'start_date', 'end_date', 'is_completed', 'percentage')


class WorkHistoryInline(admin.TabularInline):
    """Inline admin for Work History"""
    model = WorkHistory
    extra = 1
    fields = ('company_name', 'job_title', 'start_date', 'end_date', 'is_current', 'salary')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeAdminForm
    list_display = (
        'employee_id', 'get_full_name', 'email', 'role', 'department', 
        'designation', 'employment_status', 'is_active', 'joining_date'
    )
    list_filter = (
        'role', 'employment_status', 'employee_type', 'department', 
        'designation', 'is_active', 'joining_date', 'created_at'
    )
    search_fields = (
        'employee_id', 'first_name', 'last_name', 'email', 
        'phone', 'pan_number', 'aadhar_number'
    )
    readonly_fields = ('employee_id', 'created_at', 'updated_at', 'created_by', 'updated_by')
    
    inlines = [EmergencyContactInline, EducationInline, WorkHistoryInline]
    
    fieldsets = (
        ('Core Information', {
            'fields': ('employee_id', 'user', 'first_name', 'middle_name', 'last_name')
        }),
        ('Personal Information', {
            'fields': (
                'date_of_birth', 'gender', 'marital_status', 
                'nationality', 'blood_group', 'photo'
            ),
            'classes': ('collapse',)
        }),
        ('Contact Information', {
            'fields': (
                'email', 'phone', 'alternate_phone',
                'address_line1', 'address_line2', 'city', 
                'state', 'country', 'postal_code'
            )
        }),
        ('Professional Information', {
            'fields': (
                'role', 'department', 'designation', 'reporting_manager',
                'employee_type', 'employment_status', 'joining_date',
                'probation_end_date', 'confirmation_date', 'work_location'
            )
        }),
        ('Identification Documents', {
            'fields': ('pan_number', 'aadhar_number', 'passport_number', 'driving_license'),
            'classes': ('collapse',)
        }),
        ('Financial Information', {
            'fields': ('bank_name', 'account_number', 'ifsc_code', 'account_holder_name'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter user field to only show verified users who don't have an employee profile"""
        if db_field.name == "user":
            # Only show verified, active users who don't already have an employee profile
            kwargs["queryset"] = User.objects.filter(
                is_verified=True,
                is_active=True
            ).exclude(
                employee_profile__isnull=False
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by, and auto-populate from user if available"""
        if not change and obj.user and obj.user.is_verified:
            # Auto-populate fields from user if they're empty
            if not obj.first_name and obj.user.first_name:
                obj.first_name = obj.user.first_name
            if not obj.last_name and obj.user.last_name:
                obj.last_name = obj.user.last_name
            if not obj.email and obj.user.email:
                obj.email = obj.user.email
            if not obj.phone and obj.user.phone_number:
                obj.phone = obj.user.phone_number
            if not obj.gender and obj.user.gender:
                # Map User gender (M/F/O) to Employee gender (male/female/other)
                gender_map = {'M': 'male', 'F': 'female', 'O': 'other'}
                obj.gender = gender_map.get(obj.user.gender, '')
            if not obj.photo and obj.user.photo:
                obj.photo = obj.user.photo
        
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee', 'relationship', 'phone', 'is_primary')
    list_filter = ('is_primary', 'relationship', 'created_at')
    search_fields = ('name', 'employee__first_name', 'employee__last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'employee', 'institution', 'level', 'is_completed', 'end_date')
    list_filter = ('level', 'is_completed', 'created_at')
    search_fields = ('degree', 'employee__first_name', 'employee__last_name', 'institution')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WorkHistory)
class WorkHistoryAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'job_title', 'employee', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current', 'start_date', 'created_at')
    search_fields = ('company_name', 'job_title', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': (
                'can_view_all_employees', 'can_create_employees',
                'can_edit_all_employees', 'can_delete_employees',
                'can_view_subordinates', 'can_approve_leave',
                'can_approve_timesheet'
            )
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
