from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .emails import send_verification_email
from .forms import CustomUserCreationForm
from employees.models import Employee
from django.db import transaction


class CustomUserAdmin(UserAdmin):
    model = User
    add_form = CustomUserCreationForm

    list_display = ("username", "email", "first_name", "last_name", "job_title", "is_verified", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "phone_number", "gender", "photo")}),
        ("Professional Info", {"fields": ("job_title", "department")}),
        ("Account Status", {"fields": ("is_verified", "is_first_login")}),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "first_name",
                "last_name",
                "password1",
                "password2",
                "phone_number",
                "gender",
                "job_title",
                "department",
                "form_department",
                "form_designation",
                "form_reporting_manager",
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        🔐 On admin-created user:
        - lock account
        - mark unverified
        - send verification email
        - auto-create employee profile
        """
        is_new_user = obj.pk is None

        if is_new_user:
            obj.is_active = False
            obj.is_verified = False

        with transaction.atomic():
            super().save_model(request, obj, form, change)

            if is_new_user:
                # Extract employee data from form
                phone = form.cleaned_data.get('phone_number')
                department = form.cleaned_data.get('form_department')
                designation = form.cleaned_data.get('form_designation')
                reporting_manager = form.cleaned_data.get('form_reporting_manager')

                # Create Employee profile
                Employee.objects.create(
                    user=obj,
                    first_name=obj.first_name,
                    last_name=obj.last_name,
                    email=obj.email,
                    phone=phone,
                    department=department,
                    designation=designation,
                    reporting_manager=reporting_manager,
                    created_by=request.user,
                    updated_by=request.user,
                )

                send_verification_email(obj)


admin.site.register(User, CustomUserAdmin)
