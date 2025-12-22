from django.contrib import admin
from .models import Leave, LeaveQuota, LeaveBalance, RestrictedHoliday

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'from_date', 'to_date', 'no_of_days', 'status', 'created_at')
    list_filter = ('status', 'leave_type', 'created_at')
    search_fields = ('employee__first_name', 'employee__email', 'reason')
    date_hierarchy = 'from_date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Leave Details', {
            'fields': ('employee', 'leave_type', 'from_date', 'to_date', 'no_of_days', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Additional Info', {
            'fields': ('day_status', 'late_reason', 'doc_link', 'rh_dates'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LeaveQuota)
class LeaveQuotaAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'yearly_quota', 'monthly_quota', 'rh_quota', 'carry_forward_limit', 'effective_from', 'effective_to')
    list_filter = ('leave_type', 'effective_from')
    search_fields = ('employee__first_name', 'employee__email')
    date_hierarchy = 'effective_from'
    
    fieldsets = (
        ('Employee & Leave Type', {
            'fields': ('employee', 'leave_type')
        }),
        ('Quota Configuration', {
            'fields': ('monthly_quota', 'yearly_quota', 'rh_quota', 'carry_forward_limit')
        }),
        ('Validity Period', {
            'fields': ('effective_from', 'effective_to')
        }),
    )


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_allocated', 'used', 'pending', 'get_available', 'carried_forward', 'rh_allocated', 'rh_used', 'get_rh_available')
    list_filter = ('year', 'leave_type')
    search_fields = ('employee__first_name', 'employee__email')
    readonly_fields = ('get_available', 'get_rh_available', 'created_at', 'updated_at')
    
    def get_available(self, obj):
        return obj.available
    get_available.short_description = 'Available'
    
    def get_rh_available(self, obj):
        return obj.rh_available
    get_rh_available.short_description = 'RH Available'
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'leave_type', 'year')
        }),
        ('Allocation', {
            'fields': ('total_allocated', 'carried_forward')
        }),
        ('Usage', {
            'fields': ('used', 'pending', 'get_available')
        }),
        ('RH Tracking', {
            'fields': ('rh_allocated', 'rh_used', 'get_rh_available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RestrictedHoliday)
class RestrictedHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_active', 'created_at')
    list_filter = ('is_active', 'date')
    search_fields = ('name', 'description')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Holiday Details', {
            'fields': ('name', 'date', 'description', 'is_active')
        }),
    )
