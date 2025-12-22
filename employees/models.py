from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from auth_app.models import User


class Employee(models.Model):
    """Main Employee model"""
    
    # Employment Type Choices
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
        ('consultant', 'Consultant'),
    ]
    
    # Employment Status Choices
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
        ('suspended', 'Suspended'),
        ('resigned', 'Resigned'),
    ]
    
    # Gender Choices
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer Not to Say'),
    ]
    
    # Marital Status Choices
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]

    # ========== CORE IDENTIFICATION ==========
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique employee identifier"
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        null=True,
        blank=True,
        help_text="Link to user account for login"
    )
    
    # ========== PERSONAL INFORMATION ==========
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True
    )
    nationality = models.CharField(max_length=50, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    photo = models.ImageField(
        upload_to='employee_photos/',
        null=True,
        blank=True,
        help_text="Employee profile photo"
    )
    
    # ========== CONTACT INFORMATION ==========
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    alternate_phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, default='India')
    postal_code = models.CharField(max_length=10, blank=True)
    
    # ========== PROFESSIONAL INFORMATION ==========
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='employees'
    )
    designation = models.ForeignKey(
        'departments.Designation',
        on_delete=models.PROTECT,
        related_name='employees'
    )
    reporting_manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        help_text="Direct reporting manager"
    )
    employee_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='full_time'
    )
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='active'
    )
    joining_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)
    work_location = models.CharField(max_length=100, default='Office')
    
    # ========== IDENTIFICATION DOCUMENTS ==========
    pan_number = models.CharField(max_length=10, blank=True, unique=True, null=True)
    aadhar_number = models.CharField(max_length=12, blank=True, unique=True, null=True)
    passport_number = models.CharField(max_length=20, blank=True, unique=True, null=True)
    driving_license = models.CharField(max_length=20, blank=True)
    
    # ========== FINANCIAL INFORMATION ==========
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    account_holder_name = models.CharField(max_length=100, blank=True)
    
    # ========== SYSTEM FIELDS ==========
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_employees'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_employees'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['email']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['department', 'designation']),
        ]
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

    def get_full_name(self):
        """Return full name of employee"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Property for full name"""
        return self.get_full_name()

    def save(self, *args, **kwargs):
        """Auto-generate employee_id if not provided"""
        if not self.employee_id:
            # Generate employee_id: EMP + year + auto-increment
            from django.utils import timezone
            year = timezone.now().year
            last_employee = Employee.objects.filter(
                employee_id__startswith=f'EMP{year}'
            ).order_by('-employee_id').first()
            
            if last_employee:
                try:
                    last_num = int(last_employee.employee_id[-4:])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            
            self.employee_id = f'EMP{year}{str(new_num).zfill(4)}'
        
        super().save(*args, **kwargs)


class EmergencyContact(models.Model):
    """Emergency Contact model - Multiple contacts per employee"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )
    name = models.CharField(max_length=100)
    relationship = models.CharField(
        max_length=50,
        help_text="e.g., Spouse, Father, Mother, Sibling, Friend"
    )
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary emergency contact"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', 'name']
        verbose_name = 'Emergency Contact'
        verbose_name_plural = 'Emergency Contacts'

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.employee.get_full_name()}"

    def save(self, *args, **kwargs):
        """Ensure only one primary contact per employee"""
        if self.is_primary:
            EmergencyContact.objects.filter(
                employee=self.employee,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Education(models.Model):
    """Education/Qualification model - Multiple education records per employee"""
    # Education Level Choices
    EDUCATION_LEVEL_CHOICES = [
        ('high_school', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('phd', 'PhD'),
        ('certification', 'Certification'),
        ('other', 'Other'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='educations'
    )
    level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES
    )
    degree = models.CharField(
        max_length=100,
        help_text="e.g., B.Tech, MBA, B.Sc"
    )
    field_of_study = models.CharField(
        max_length=100,
        help_text="e.g., Computer Science, Business Administration"
    )
    institution = models.CharField(
        max_length=200,
        help_text="School/University name"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=True)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage or CGPA"
    )
    grade = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    certificate = models.FileField(
        upload_to='education_certificates/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-start_date']
        verbose_name = 'Education'
        verbose_name_plural = 'Educations'

    def __str__(self):
        return f"{self.degree} - {self.employee.get_full_name()}"

    def clean(self):
        """Validate dates"""
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError("End date cannot be before start date.")


class WorkHistory(models.Model):
    """Work History model - Previous employment records"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='work_histories'
    )
    company_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(
        default=False,
        help_text="Is this the current job?"
    )
    job_description = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    reason_for_leaving = models.TextField(blank=True)
    supervisor_name = models.CharField(max_length=100, blank=True)
    supervisor_contact = models.CharField(max_length=50, blank=True)
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Last drawn salary"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-start_date']
        verbose_name = 'Work History'
        verbose_name_plural = 'Work Histories'

    def __str__(self):
        return f"{self.job_title} at {self.company_name} - {self.employee.get_full_name()}"

    def clean(self):
        """Validate dates"""
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError("End date cannot be before start date.")
