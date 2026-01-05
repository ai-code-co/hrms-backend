from rest_framework import serializers
from .models import Leave, LeaveQuota, LeaveBalance, RestrictedHoliday
from django.utils import timezone
from datetime import datetime
import os

class LeaveSerializer(serializers.ModelSerializer):
    no_of_days = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=False, default=1.0)
    is_restricted = serializers.SerializerMethodField()
    doc_link_url = serializers.SerializerMethodField(read_only=True)
    rh_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    def get_is_restricted(self, obj):
        return obj.leave_type == Leave.LeaveType.RESTRICTED_HOLIDAY

    class Meta:
        model = Leave
        fields = [
            'id', 'from_date', 'to_date', 'no_of_days', 'reason', 
            'leave_type', 'is_restricted', 'status', 'day_status', 'late_reason', 
            'doc_link', 'doc_link_url', 'rejection_reason', 'rh_dates', 'created_at' ,'rh_id', 'restricted_holiday'
        ]
        read_only_fields = ['created_at', 'doc_link_url', 'restricted_holiday', 'is_restricted']
    
    def update(self, instance, validated_data):
        """Override update to enforce permission checks on status changes"""
        request = self.context.get('request')
        new_status = validated_data.get('status')
        
        # If status is being changed
        if new_status and new_status != instance.status:
            user = request.user if request else None
            
            # Check permissions for status change
            if new_status in ['Approved', 'Rejected']:
                # Only admins can approve/reject
                if not user or not user.is_staff:
                    raise serializers.ValidationError({
                        'status': 'Only administrators can approve or reject leaves.'
                    })
                
                # If rejecting, rejection_reason is required
                if new_status == 'Rejected' and not validated_data.get('rejection_reason'):
                    raise serializers.ValidationError({
                        'rejection_reason': 'Rejection reason is required when rejecting a leave.'
                    })
            
            elif new_status == 'Cancelled':
                # Users can cancel their own leaves
                # Admins can cancel any leave
                if not user or (not user.is_staff and instance.employee.user != user):
                    raise serializers.ValidationError({
                        'status': 'You can only cancel your own leaves.'
                    })
                
                # Can only cancel pending leaves
                if instance.status != 'Pending':
                    raise serializers.ValidationError({
                        'status': f'Cannot cancel a leave that is already {instance.status}. Only Pending leaves can be cancelled.'
                    })
        
        return super().update(instance, validated_data)
    
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
        # Skip validation for updates (only validate on creation)
        if self.instance is not None:
            return data
        
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
        from_date = data.get('from_date')
        
        # NEW LOGIC: RH Validation
        rh_id = data.get('rh_id')
        
        if leave_type == 'Restricted Holiday':
            if not rh_id:
                raise serializers.ValidationError({"rh_id": "Please select a Restricted Holiday."})
            
            try:
                # Check if RH exists and is active
                rh_obj = RestrictedHoliday.objects.get(id=rh_id, is_active=True)
            except RestrictedHoliday.DoesNotExist:
                raise serializers.ValidationError({"rh_id": "Invalid or inactive Restricted Holiday selected."})

            # Validate that the leave date is not before the holiday date
            if from_date < rh_obj.date:
                 raise serializers.ValidationError({
                     "from_date": f"Restricted Holiday leave cannot be taken before the actual holiday date ({rh_obj.date})."
                 })
            
            # Save the object in data temporarily to use in create()
            data['restricted_holiday_obj'] = rh_obj
        # Get current year
        current_year = timezone.now().year
        
        # Check leave balance
        try:
            # Special case: Restricted Holiday balance is often tracked on the Casual Leave record
            target_leave_type = leave_type
            if leave_type == 'Restricted Holiday':
                 target_leave_type = 'Casual Leave'
                 
            balance = LeaveBalance.objects.get(
                employee=employee,
                leave_type=target_leave_type,
                year=current_year
            )
            
                # Balance Check for Restricted Holiday
            if leave_type == 'Restricted Holiday':
                # Assuming 1 RH application = 1 unit of RH balance
                if balance.rh_available < 1:
                     raise serializers.ValidationError({
                        'non_field_errors': f'Insufficient Restricted Holiday balance. Available: {balance.rh_available}'
                    })
            else:
                # Balance Check for Regular Leaves
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

    def create(self, validated_data):
        """Custom create to handle the Restricted Holiday ForeignKey"""
        
        # Pop the helper object and the integer ID
        rh_obj = validated_data.pop('restricted_holiday_obj', None)
        validated_data.pop('rh_id', None)
        
        # Create the Leave instance
        leave = Leave.objects.create(**validated_data)
        
        # If it was an RH application, link the ForeignKey
        if rh_obj:
            leave.restricted_holiday = rh_obj
            leave.save()
            
        return leave


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
