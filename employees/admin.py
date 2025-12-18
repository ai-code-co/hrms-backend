from django.contrib import admin
from .models import Employee, EmergencyContact, Education, WorkHistory


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
    list_display = (
        'employee_id', 'get_full_name', 'email', 'department', 
        'designation', 'employment_status', 'is_active', 'joining_date'
    )
    list_filter = (
        'employment_status', 'employee_type', 'department', 
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
                'department', 'designation', 'reporting_manager',
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
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by"""
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
