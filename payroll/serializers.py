from rest_framework import serializers
from .models import SalaryStructure, Payslip, PayrollConfig

class PayslipSummarySerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()
    statement_reference = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    total_net_salary = serializers.CharField(source='net_salary')

    class Meta:
        model = Payslip
        fields = [
            'id', 'month', 'year', 'month_name', 'formatted_date', 
            'status', 'total_net_salary', 'statement_reference'
        ]

    def get_status(self, obj):
        return obj.status.capitalize()

    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]

    def get_formatted_date(self, obj):
        import calendar
        from datetime import date
        # Return the last day of the month for display
        last_day = calendar.monthrange(obj.year, obj.month)[1]
        return date(obj.year, obj.month, last_day).strftime("%b %d, %Y")

    def get_statement_reference(self, obj):
        return f"PAY-{str(obj.year)[2:]}-{obj.month:02d}-{obj.id:03d}"

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
    
    month_name = serializers.SerializerMethodField()
    statement_reference = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    earnings_breakdown = serializers.SerializerMethodField()
    deductions_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = Payslip
        fields = [
            'id', 'user_Id', 'month', 'year', 'month_name', 'total_leave_taken', 'leave_balance',
            'allocated_leaves', 'paid_leaves', 'unpaid_leaves', 'final_leave_balance',
            'status', 'misc_deduction_2', 'bonus', 'total_working_days',
            'total_earnings', 'total_deductions', 'total_taxes', 'total_net_salary',
            'statement_reference', 'bank_details', 'earnings_breakdown', 'deductions_breakdown'
        ]

    def get_status(self, obj):
        # UI expects "Paid" or similar, but the payload has a code or status string
        return obj.status.capitalize()

    def get_month(self, obj):
        return f"{obj.month:02d}"

    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]

    def get_statement_reference(self, obj):
        # Format: PAY-YY-MM-XXX
        return f"PAY-{str(obj.year)[2:]}-{obj.month:02d}-{obj.id:03d}"

    def get_bank_details(self, obj):
        employee = obj.employee
        return {
            "bank_name": employee.bank_name,
            "account_number": employee.account_number,
            "masked_account_number": f"**** {employee.account_number[-4:]}" if employee.account_number else ""
        }

    def get_earnings_breakdown(self, obj):
        items = [
            {"label": "Basic Salary", "amount": float(obj.basic_salary)},
            {"label": "HRA", "amount": float(obj.hra)},
            {"label": "Special Allowance", "amount": float(obj.special_allowance)},
            {"label": "Medical Allowance", "amount": float(obj.medical_allowance)},
            {"label": "Conveyance Allowance", "amount": float(obj.conveyance_allowance)},
            {"label": "Bonus", "amount": float(obj.bonus)},
            {"label": "Arrears", "amount": float(obj.arrears)},
        ]
        return [item for item in items if item["amount"] > 0]

    def get_deductions_breakdown(self, obj):
        items = [
            {"label": "Tax (TDS)", "amount": float(obj.tds)},
            {"label": "Provident Fund", "amount": float(obj.epf)},
            {"label": "Loan Deduction", "amount": float(obj.loan_deduction)},
            {"label": "Advance Deduction", "amount": float(obj.advance_deduction)},
            {"label": "Unpaid Leave Deduction", "amount": float(obj.unpaid_leave_deduction)},
            {"label": "Misc Deduction", "amount": float(obj.misc_deduction)},
            {"label": "Professional Tax", "amount": float(obj.misc_deduction_2)}, # Mapping misc_deduction_2 to Professional Tax or Health Insurance
        ]
        return [item for item in items if item["amount"] > 0]

class SalaryOverviewSerializer(serializers.Serializer):
    id = serializers.CharField(source='employee.id')
    name = serializers.CharField(source='employee.get_full_name')
    email = serializers.EmailField(source='employee.email')
    date_of_joining = serializers.DateField(source='employee.joining_date')
    type = serializers.CharField(default='employee')
    annual_ctc = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    salary_details = SalaryStructureSerializer(many=True)
    holding_details = serializers.ListField(default=[])
    payslip_months = PayslipSummarySerializer(many=True)
    selected_payslip = PayslipSerializer()

    def get_annual_ctc(self, obj):
        # latest_structure is the last one in the list (ordered by applicable_from)
        salary_details = obj.get('salary_details', [])
        if salary_details:
            latest = salary_details[len(salary_details)-1]
            return float(latest.total_earnings * 12)
        return 0

    def get_bank_details(self, obj):
        # employee is available in the context or we can fetch it if passed as dict
        # In UserSalaryInfoView, data is a dict
        # But wait, SalaryOverviewSerializer is used where?
        return {}

class PayrollConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollConfig
        fields = ['key', 'value', 'description']
