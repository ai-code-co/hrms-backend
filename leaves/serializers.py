from rest_framework import serializers
from .models import Leave, LeaveQuota, LeaveBalance, RestrictedHoliday
from django.utils import timezone
from datetime import datetime
import os

class LeaveSerializer(serializers.ModelSerializer):
    no_of_days = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=False, default=1.0)
    doc_link_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Leave
        fields = [
            'id', 'from_date', 'to_date', 'no_of_days', 'reason', 
            'leave_type', 'status', 'day_status', 'late_reason', 
            'doc_link', 'doc_link_url', 'rejection_reason', 'rh_dates', 'created_at'
        ]
        read_only_fields = ['status', 'rejection_reason', 'created_at', 'doc_link_url']
    
    def get_doc_link_url(self, obj):
        """Construct full Cloudinary URL from stored path"""
        if not obj.doc_link:
            return None
        
        # Get Cloudinary base URL from environment or use default
        cloudinary_base = os.getenv('CLOUDINARY_BASE_URL', 'https://res.cloudinary.com/dhlyvqdoi/image/upload')
        
        # Construct full URL
        # If path already has version (v1234567890), use as-is
        # Otherwise, add a default version
        if obj.doc_link.startswith('http'):
            # Already a full URL, return as-is (backward compatibility)
            return obj.doc_link
        
        # Construct URL from path
        return f"{cloudinary_base}/{obj.doc_link}"
    
    def validate(self, data):
        """Validate leave application against balance"""
        # OLD CODE (Before 2025-12-22): Used request.user directly
        # employee = self.context['request'].user
        
        # NEW CODE (2025-12-22): Get Employee from User
        user = self.context['request'].user
        
        # Check if user has employee profile
        if not hasattr(user, 'employee_profile'):
            raise serializers.ValidationError({
                'employee': 'User must have an employee profile to apply for leaves. Please contact HR.'
            })
        
        employee = user.employee_profile
        leave_type = data.get('leave_type')
        no_of_days = data.get('no_of_days', 0)
        rh_dates = data.get('rh_dates', [])
        
        # Get current year
        current_year = timezone.now().year
        
        # Check leave balance
        try:
            balance = LeaveBalance.objects.get(
                employee=employee,
                leave_type=leave_type,
                year=current_year
            )
            
            if balance.available < no_of_days:
                raise serializers.ValidationError({
                    'no_of_days': f'Insufficient leave balance. Available: {balance.available}, Requested: {no_of_days}'
                })
            
            # Check RH balance if RH dates provided
            if rh_dates and len(rh_dates) > balance.rh_available:
                raise serializers.ValidationError({
                    'rh_dates': f'Insufficient RH balance. Available: {balance.rh_available}, Requested: {len(rh_dates)}'
                })
                
        except LeaveBalance.DoesNotExist:
            raise serializers.ValidationError({
                'leave_type': f'No leave quota configured for {leave_type}. Please contact HR.'
            })
        
        return data


class LeaveQuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveQuota
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):
    available = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    rh_available = serializers.IntegerField(read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'year',
            'total_allocated', 'carried_forward', 'used', 'pending',
            'available', 'rh_allocated', 'rh_used', 'rh_available'
        ]
        read_only_fields = ['used', 'pending']


class RestrictedHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = RestrictedHoliday
        fields = '__all__'


class LeaveCalculationSerializer(serializers.Serializer):
    """
    Serializer to validate input for calculate-days API
    """
    start_date = serializers.DateField()
    end_date = serializers.DateField()
