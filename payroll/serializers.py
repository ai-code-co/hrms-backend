from rest_framework import serializers
from .models import SalaryStructure, Payslip, PayrollConfig

class SalaryStructureSerializer(serializers.ModelSerializer):
    # Mapping to match the user's specific naming in the prototype
    Special_Allowance = serializers.DecimalField(source='special_allowance', max_digits=12, decimal_places=2)
    Medical_Allowance = serializers.DecimalField(source='medical_allowance', max_digits=12, decimal_places=2)
    Conveyance = serializers.DecimalField(source='conveyance_allowance', max_digits=12, decimal_places=2)
    HRA = serializers.DecimalField(source='hra', max_digits=12, decimal_places=2)
    Basic = serializers.DecimalField(source='basic_salary', max_digits=12, decimal_places=2)
    EPF = serializers.DecimalField(source='epf', max_digits=12, decimal_places=2)
    TDS = serializers.DecimalField(source='tds', max_digits=12, decimal_places=2)
    
    total_earning = serializers.SerializerMethodField()
    total_deduction = serializers.SerializerMethodField()
    total_net_salary = serializers.SerializerMethodField()
    
    # Generic placeholders to match prototype
    Arrears = serializers.CharField(default="0")
    Increment_Amount = serializers.CharField(default="0")
    Misc_Deductions = serializers.CharField(default="0")
    Advance = serializers.CharField(default="0")
    Loan = serializers.CharField(default="0")
    total_holding_amount = serializers.IntegerField(default=0)
    
    date = serializers.SerializerMethodField()

    class Meta:
        model = SalaryStructure
        fields = [
            'Basic', 'HRA', 'Medical_Allowance', 'Conveyance', 'Special_Allowance',
            'EPF', 'TDS', 'Arrears', 'Increment_Amount', 'Misc_Deductions', 
            'Advance', 'Loan', 'total_holding_amount', 'total_earning', 
            'total_deduction', 'total_net_salary', 'date'
        ]

    def get_total_earning(self, obj):
        return obj.total_earnings

    def get_total_deduction(self, obj):
        return obj.epf + obj.tds

    def get_total_net_salary(self, obj):
        return self.get_total_earning(obj) - self.get_total_deduction(obj)

    def get_date(self, obj):
        # Using created_at or joining_date
        return obj.employee.joining_date if obj.employee.joining_date else obj.created_at.date()

class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = [
            'id', 'month', 'year', 'working_days', 
            'total_earnings', 'total_deductions', 'net_salary',
            'leaves_taken', 'unpaid_leaves', 'bonus', 'status'
        ]
        # Adding some extra aliases to match frontend expectations if needed
        # But keeping it clean for now.

class SalaryOverviewSerializer(serializers.Serializer):
    id = serializers.CharField(source='employee.user.id')
    name = serializers.CharField(source='employee.get_full_name')
    email = serializers.EmailField(source='employee.email')
    date_of_joining = serializers.DateField(source='employee.joining_date')
    type = serializers.CharField(default='employee')
    salary_details = SalaryStructureSerializer(many=True) # Usually one, but prototype shows a list
    payslip_history = PayslipSerializer(many=True)
    holding_details = serializers.ListField(default=[])

class PayrollConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollConfig
        fields = ['key', 'value', 'description']
