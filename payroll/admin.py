from django.contrib import admin
from .models import SalaryStructure, Payslip, PayrollConfig

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('employee', 'basic_salary', 'total_earnings', 'is_active')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__user__username')
    list_filter = ('is_active',)

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'net_salary', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('year', 'month', 'status')
    readonly_fields = ('generated_at',)

@admin.register(PayrollConfig)
class PayrollConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'updated_at')
    search_fields = ('key',)
