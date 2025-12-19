from django.contrib import admin
from .models import Holiday


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    """Admin interface for Holiday model"""
    list_display = [
        'name', 'date', 'country', 'region', 
        'holiday_type', 'is_active', 'created_at'
    ]
    list_filter = [
        'holiday_type', 'country', 'is_active', 
        'date', 'created_at'
    ]
    search_fields = ['name', 'description', 'country', 'region']
    date_hierarchy = 'date'
    ordering = ['-date', 'name']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'date', 'description')
        }),
        ('Location', {
            'fields': ('country', 'region')
        }),
        ('Settings', {
            'fields': ('holiday_type', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


