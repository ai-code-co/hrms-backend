from rest_framework import serializers
from .models import Department, Designation


class DesignationSerializer(serializers.ModelSerializer):
    """Serializer for Designation"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Designation
        fields = [
            'id', 'name', 'department', 'department_name', 
            'level', 'description', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department"""
    designations = DesignationSerializer(many=True, read_only=True)
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description', 'manager', 
            'manager_name', 'is_active', 'employee_count',
            'designations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_employee_count(self, obj):
        """Get count of active employees in department"""
        return obj.employees.filter(is_active=True).count()


class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for department lists"""
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'is_active', 'employee_count']
    
    def get_employee_count(self, obj):
        return obj.employees.filter(is_active=True).count()

