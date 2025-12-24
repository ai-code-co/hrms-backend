from rest_framework import serializers
from .models import Holiday


class HolidayListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for holiday lists"""
    
    class Meta:
        model = Holiday
        fields = [
            'id', 'name', 'date', 'country', 
            'region', 'holiday_type', 'is_active'
        ]


class HolidaySerializer(serializers.ModelSerializer):
    """Full serializer for holiday details"""
    
    holiday_type_display = serializers.CharField(
        source='get_holiday_type_display',
        read_only=True
    )
    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Holiday
        fields = [
            'id', 'name', 'date', 'description', 
            'country', 'region', 'holiday_type', 
            'holiday_type_display', 'is_active',
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 
            'created_by', 'updated_by'
        ]
    
    def get_created_by_name(self, obj):
        """Get the name of user who created this holiday"""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None
    
    def get_updated_by_name(self, obj):
        """Get the name of user who last updated this holiday"""
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.email
        return None
