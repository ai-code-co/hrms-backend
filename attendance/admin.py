from django.contrib import admin
from .models import Attendance
from .constants import TIME_12HR_FORMAT


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'date', 'get_in_time', 'get_out_time', 
        'get_office_time', 'get_home_time',
        'day_type', 'get_total_time', 'get_extra_time', 
        'admin_alert', 'is_working_from_home', 'created_at'
    )
    list_filter = (
        'day_type', 'admin_alert', 'is_working_from_home', 'date', 'created_at',
        'employee__department', 'employee__designation'
    )
    search_fields = (
        'employee__first_name', 'employee__last_name', 
        'employee__employee_id', 'date', 'admin_alert_message'
    )
    readonly_fields = (
        'seconds_actual_worked_time', 'seconds_actual_working_time',
        'seconds_extra_time', 'office_time_inside', 'extra_time_status',
        'office_seconds_worked', 'home_seconds_worked',
        'created_at', 'updated_at', 'created_by', 'updated_by'
    )
    
    fieldsets = (
        ('Employee & Date', {
            'fields': ('employee', 'date', 'day_type', 'is_day_before_joining', 'is_working_from_home')
        }),
        ('Check-in/Check-out (Backward Compatible)', {
            'fields': ('in_time', 'out_time'),
            'classes': ('collapse',)
        }),
        ('Location Times', {
            'fields': (
                ('office_in_time', 'office_out_time'),
                ('home_in_time', 'home_out_time'),
                ('office_seconds_worked', 'home_seconds_worked')
            )
        }),
        ('Working Hours', {
            'fields': (
                'office_working_hours', 'orignal_total_time',
                'seconds_actual_worked_time', 'seconds_actual_working_time',
                'seconds_extra_time', 'office_time_inside', 'extra_time_status'
            )
        }),
        ('Alerts & Messages', {
            'fields': ('admin_alert', 'admin_alert_message', 'day_text', 'text')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_in_time(self, obj):
        """Format in_time for display"""
        if obj.in_time:
            return obj.in_time.strftime(TIME_12HR_FORMAT)
        return "-"
    get_in_time.short_description = 'Check-in'
    
    def get_out_time(self, obj):
        """Format out_time for display"""
        if obj.out_time:
            return obj.out_time.strftime(TIME_12HR_FORMAT)
        return "-"
    get_out_time.short_description = 'Check-out'
    
    def get_total_time(self, obj):
        """Format total time for display"""
        if obj.seconds_actual_worked_time:
            hours = obj.seconds_actual_worked_time // 3600
            minutes = (obj.seconds_actual_worked_time % 3600) // 60
            return f"{hours}h {minutes}m"
        return "-"
    get_total_time.short_description = 'Total Time'
    
    def get_extra_time(self, obj):
        """Format extra time for display"""
        if obj.seconds_extra_time:
            hours = abs(obj.seconds_extra_time) // 3600
            minutes = (abs(obj.seconds_extra_time) % 3600) // 60
            sign = "+" if obj.seconds_extra_time > 0 else "-"
            return f"{sign}{hours}h {minutes}m"
        return "-"
    get_extra_time.short_description = 'Extra Time'
    
    def get_office_time(self, obj):
        """Format office time range for display"""
        if obj.office_in_time and obj.office_out_time:
            in_str = obj.office_in_time.strftime(TIME_12HR_FORMAT)
            out_str = obj.office_out_time.strftime(TIME_12HR_FORMAT)
            hours = obj.office_seconds_worked // 3600
            minutes = (obj.office_seconds_worked % 3600) // 60
            return f"{in_str} - {out_str} ({hours}h {minutes}m)"
        elif obj.office_in_time:
            return f"{obj.office_in_time.strftime(TIME_12HR_FORMAT)} - (not checked out)"
        return "-"
    get_office_time.short_description = 'Office Time'
    
    def get_home_time(self, obj):
        """Format home time range for display"""
        if obj.home_in_time and obj.home_out_time:
            in_str = obj.home_in_time.strftime(TIME_12HR_FORMAT)
            out_str = obj.home_out_time.strftime(TIME_12HR_FORMAT)
            hours = obj.home_seconds_worked // 3600
            minutes = (obj.home_seconds_worked % 3600) // 60
            return f"{in_str} - {out_str} ({hours}h {minutes}m)"
        elif obj.home_in_time:
            return f"{obj.home_in_time.strftime(TIME_12HR_FORMAT)} - (not checked out)"
        return "-"
    get_home_time.short_description = 'Home Time'
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

