from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from departments.models import Department, Designation

class CustomUserCreationForm(UserCreationForm):
    """
    Custom form for creating a user in the Admin interface
    with additional fields for automatic Employee profile creation.
    """
    phone_number = forms.CharField(
        max_length=20, 
        required=True,
        help_text="Employee's primary phone number"
    )
    form_department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=True,
        help_text="Department assignment"
    )
    form_designation = forms.ModelChoiceField(
        queryset=Designation.objects.filter(is_active=True),
        required=True,
        help_text="Designation assignment"
    )
    form_reporting_manager = forms.ModelChoiceField(
        queryset=None,
        required=False,
        help_text="Direct reporting manager"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from employees.models import Employee
        self.fields['form_reporting_manager'].queryset = Employee.objects.filter(employment_status='active')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            "email", "first_name", "last_name", 
            "phone_number", "gender", "job_title",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
