from rest_framework import serializers
from .models import SalaryStructure, Payslip, PayrollConfig

class SalaryStructureSerializer(serializers.ModelSerializer):
    # Mapping to match the user's specific naming in the prototype
    Special_Allowance = serializers.SerializerMethodField()
    Medical_Allowance = serializers.SerializerMethodField()
    Conveyance = serializers.SerializerMethodField()
    HRA = serializers.SerializerMethodField()
    Basic = serializers.SerializerMethodField()
    EPF = serializers.SerializerMethodField()
    TDS = serializers.SerializerMethodField()
    
    total_earning = serializers.SerializerMethodField()
    total_deduction = serializers.SerializerMethodField()
    total_net_salary = serializers.SerializerMethodField()
    
    # Generic placeholders to match prototype (as strings)
    Arrears = serializers.CharField(default="0")
    Increment_Amount = serializers.SerializerMethodField()
    Misc_Deductions = serializers.CharField(default="0")
    Advance = serializers.CharField(default="0")
    Loan = serializers.CharField(default="0")
    total_holding_amount = serializers.IntegerField(default=0)
    
    date = serializers.DateField(source='applicable_from')
    test = serializers.SerializerMethodField()

    class Meta:
        model = SalaryStructure
        fields = [
            'Special_Allowance', 'Medical_Allowance', 'Conveyance', 'HRA', 'Basic',
            'Arrears', 'Increment_Amount', 'TDS', 'Misc_Deductions', 'Advance',
            'Loan', 'EPF', 'total_holding_amount', 'total_earning',
            'total_deduction', 'total_net_salary', 'test', 'date'
        ]

    def get_Special_Allowance(self, obj): return str(int(obj.special_allowance))
    def get_Medical_Allowance(self, obj): return str(int(obj.medical_allowance))
    def get_Conveyance(self, obj): return str(int(obj.conveyance_allowance))
    def get_HRA(self, obj): return str(int(obj.hra))
    def get_Basic(self, obj): return str(int(obj.basic_salary))
    def get_EPF(self, obj): return str(int(obj.epf))
    def get_TDS(self, obj): return str(int(obj.tds))
    def get_Increment_Amount(self, obj): return str(int(obj.increment_amount))

    def get_total_earning(self, obj): return int(obj.total_earnings)
    def get_total_deduction(self, obj): return int(obj.epf + obj.tds)
    def get_total_net_salary(self, obj): return int(obj.total_earnings - (obj.epf + obj.tds))

    def get_test(self, obj):
        # Calculate applicable month difference
        diff_months = 0
        if obj.applicable_from and obj.applicable_till:
            diff_months = (obj.applicable_till.year - obj.applicable_from.year) * 12 + \
                          (obj.applicable_till.month - obj.applicable_from.month) + 1
            
        return {
            "id": str(obj.id),
            "user_Id": str(obj.employee.id),
            "total_salary": str(int(obj.total_earnings)),
            "last_updated_on": obj.updated_at.strftime("%Y-%m-%d"),
            "updated_by": obj.updated_by.get_full_name() if obj.updated_by else "Admin",
            "leaves_allocated": str(obj.leaves_allocated),
            "applicable_from": obj.applicable_from.strftime("%Y-%m-%d") if obj.applicable_from else "",
            "applicable_till": obj.applicable_till.strftime("%Y-%m-%d") if obj.applicable_till else "",
            "applicable_month": diff_months
        }

class PayslipSerializer(serializers.ModelSerializer):
    user_Id = serializers.CharField(source='employee.id')
    total_leave_taken = serializers.CharField(source='leaves_taken')
    leave_balance = serializers.CharField()
    allocated_leaves = serializers.CharField()
    paid_leaves = serializers.CharField()
    unpaid_leaves = serializers.CharField()
    final_leave_balance = serializers.CharField()
    status = serializers.SerializerMethodField()
    misc_deduction_2 = serializers.CharField()
    bonus = serializers.CharField()
    total_working_days = serializers.CharField(source='working_days')
    total_earnings = serializers.CharField()
    total_deductions = serializers.CharField()
    total_taxes = serializers.CharField()
    total_net_salary = serializers.CharField(source='net_salary')
    
    month = serializers.SerializerMethodField()
    year = serializers.CharField()

    class Meta:
        model = Payslip
        fields = [
            'id', 'user_Id', 'month', 'year', 'total_leave_taken', 'leave_balance',
            'allocated_leaves', 'paid_leaves', 'unpaid_leaves', 'final_leave_balance',
            'status', 'misc_deduction_2', 'bonus', 'total_working_days',
            'total_earnings', 'total_deductions', 'total_taxes', 'total_net_salary'
        ]

    def get_status(self, obj):
        return "0" if obj.status in ['published', 'paid'] else "1"

    def get_month(self, obj):
        return f"{obj.month:02d}"

class SalaryOverviewSerializer(serializers.Serializer):
    id = serializers.CharField(source='employee.id')
    name = serializers.CharField(source='employee.get_full_name')
    email = serializers.EmailField(source='employee.email')
    date_of_joining = serializers.DateField(source='employee.joining_date')
    type = serializers.CharField(default='employee')
    salary_details = SalaryStructureSerializer(many=True)
    holding_details = serializers.ListField(default=[])
    payslip_history = PayslipSerializer(many=True)

class PayrollConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollConfig
        fields = ['key', 'value', 'description']
