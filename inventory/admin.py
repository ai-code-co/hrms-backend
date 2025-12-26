from django.contrib import admin
from .models import DeviceType, Device, DeviceAssignment


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    """Admin interface for DeviceType"""
    list_display = [
        'name', 'total_devices', 'working_devices', 
        'assigned_devices', 'unassigned_devices', 'is_active'
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin interface for Device"""
    list_display = [
        'id', 'device_type', 'serial_number', 'brand', 'model_name',
        'status', 'condition', 'employee', 'is_under_warranty', 'is_active'
    ]
    list_filter = [
        'device_type', 'status', 'condition', 'is_active',
        'purchase_date', 'warranty_expiry'
    ]
    search_fields = [
        'serial_number', 'model_name', 'brand', 'notes',
        'employee__first_name', 'employee__last_name', 'employee__employee_id'
    ]
    ordering = ['-created_at']
    list_editable = ['status', 'condition', 'is_active']
    raw_id_fields = ['employee', 'created_by', 'updated_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device_type', 'serial_number', 'brand', 'model_name')
        }),
        ('Status', {
            'fields': ('status', 'condition', 'is_active')
        }),
        ('Assignment', {
            'fields': ('employee',)
        }),
        ('Purchase & Warranty', {
            'fields': ('purchase_date', 'purchase_price', 'warranty_expiry')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def is_under_warranty(self, obj):
        return obj.is_under_warranty
    is_under_warranty.boolean = True
    is_under_warranty.short_description = 'Under Warranty'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DeviceAssignment)
class DeviceAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for DeviceAssignment"""
    list_display = [
        'device', 'employee', 'assigned_by', 'assigned_date',
        'returned_date', 'is_active', 'duration_days'
    ]
    list_filter = [
        'assigned_date', 'returned_date',
        'condition_at_assignment', 'condition_at_return'
    ]
    search_fields = [
        'device__serial_number', 'device__device_type__name',
        'employee__first_name', 'employee__last_name', 'employee__employee_id'
    ]
    ordering = ['-assigned_date']
    raw_id_fields = ['device', 'employee', 'assigned_by', 'returned_to']
    date_hierarchy = 'assigned_date'
    
    readonly_fields = ['assigned_date', 'duration_days']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'
