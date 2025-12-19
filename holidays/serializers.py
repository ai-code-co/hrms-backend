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
    
    class Meta:
        model = Holiday
        fields = [
            'id', 'name', 'date', 'description', 
            'country', 'region', 'holiday_type', 
            'holiday_type_display', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


