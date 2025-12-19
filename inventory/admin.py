from django.contrib import admin
from .models import DeviceType, Device, DeviceAssignment


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'total_devices', 'working_devices', 'unassigned_devices', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'total_devices', 'working_devices', 'unassigned_devices')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_devices', 'working_devices', 'unassigned_devices'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_type', 'serial_number', 'status', 'employee', 'purchase_date', 'is_active', 'created_at')
    list_filter = ('device_type', 'status', 'is_active', 'created_at', 'purchase_date')
    search_fields = ('serial_number', 'device_type__name', 'employee__first_name', 'employee__last_name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    raw_id_fields = ('employee', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device_type', 'serial_number', 'status', 'is_active')
        }),
        ('Assignment', {
            'fields': ('employee',)
        }),
        ('Purchase Details', {
            'fields': ('purchase_date', 'purchase_price', 'warranty_expiry'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields"""
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DeviceAssignment)
class DeviceAssignmentAdmin(admin.ModelAdmin):
    list_display = ('device', 'employee', 'assigned_by', 'assigned_date', 'returned_date', 'is_active')
    list_filter = ('assigned_date', 'returned_date', 'device__device_type')
    search_fields = ('device__device_type__name', 'device__serial_number', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('assigned_date',)
    raw_id_fields = ('device', 'employee', 'assigned_by')
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('device', 'employee', 'assigned_by', 'assigned_date')
        }),
        ('Return Information', {
            'fields': ('returned_date', 'notes')
        }),
    )

    def is_active(self, obj):
        """Check if assignment is active"""
        return obj.returned_date is None
    is_active.boolean = True
    is_active.short_description = 'Active'

