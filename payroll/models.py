from django.db import models
from django.conf import settings
from employees.models import Employee

class SalaryStructure(models.Model):
    """
    Defines the monthly salary components for an employee. (Historical)
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='salary_structures'
    )
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="HRA")
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    conveyance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # New fields to match the 'test' object in prototype
    applicable_from = models.DateField(null=True, blank=True)
    applicable_till = models.DateField(null=True, blank=True)
    leaves_allocated = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    increment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions/Other components
    epf = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="EPF")
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="TDS")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Salary Structure"
        verbose_name_plural = "Salary Structures"

    def __str__(self):
        return f"Salary Structure - {self.employee.get_full_name()}"

    @property
    def total_earnings(self):
        return (self.basic_salary + self.hra + self.medical_allowance + 
                self.conveyance_allowance + self.special_allowance)

class Payslip(models.Model):
    """
    Stores generated monthly payslips.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('paid', 'Paid'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='payslips',
        
    )
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    
    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    hra = models.DecimalField(max_digits=12, decimal_places=2)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2)
    conveyance_allowance = models.DecimalField(max_digits=12, decimal_places=2)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    arrears = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    epf = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    misc_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unpaid_leave_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Summaries
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Attendance/Leave info for that month
    working_days = models.IntegerField()
    leaves_taken = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    unpaid_leaves = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    leave_balance = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    allocated_leaves = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    paid_leaves = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    final_leave_balance = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    misc_deduction_2 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_payslips',
        
    )

    class Meta:
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Payslip {self.month}/{self.year} - {self.employee.get_full_name()}"

class PayrollConfig(models.Model):
    """
    Generic payroll configurations.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
