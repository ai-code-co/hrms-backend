from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .emails import send_verification_email


class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
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
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        🔐 On admin-created user:
        - lock account
        - mark unverified
        - send verification email
        """
        is_new_user = obj.pk is None

        if is_new_user:
            obj.is_active = False
            obj.is_verified = False

        super().save_model(request, obj, form, change)

        if is_new_user:
            send_verification_email(obj)


admin.site.register(User, CustomUserAdmin)
