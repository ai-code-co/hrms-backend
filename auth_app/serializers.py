from rest_framework import serializers

from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from .emails import send_verification_email
import logging

logger = logging.getLogger(__name__)

from rest_framework import serializers
from .models import User



class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "phone_number", "gender", "job_title", "department",
            # NEW employee fields
            "department_id", "designation_id", 
            "reporting_manager_id", "joining_date",
            "address_line1", "city", "state", "postal_code"
        ]

    # Handle NEW employee fields as explicitly extra fields if they are not on User model
    department_id = serializers.IntegerField(required=True)
    designation_id = serializers.IntegerField(required=True)
    reporting_manager_id = serializers.IntegerField(required=False, allow_null=True)
    joining_date = serializers.DateField(required=False, allow_null=True)
    address_line1 = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        # Extract employee-specific fields
        employee_data = {
            'phone': validated_data.get('phone_number'), # Use phone_number from User
            'department_id': validated_data.pop('department_id'),
            'designation_id': validated_data.pop('designation_id'),
            'reporting_manager_id': validated_data.pop('reporting_manager_id', None),
            'joining_date': validated_data.pop('joining_date', None),
            'address_line1': validated_data.pop('address_line1', ''),
            'city': validated_data.pop('city', ''),
            'state': validated_data.pop('state', ''),
            'postal_code': validated_data.pop('postal_code', ''),
        }

        password = validated_data.pop("password")

        user = User.objects.create(
            **validated_data,
            is_active=True,
            is_verified=True,      # Keep as True since it's admin created usually assumes verified or use flow
            is_first_login=True
        )

        user.set_password(password)
        user.save()

        # Create Employee profile
        from employees.models import Employee
        from django.utils import timezone
        
        Employee.objects.create(
            user=user,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=employee_data['phone'],
            department_id=employee_data['department_id'],
            designation_id=employee_data['designation_id'],
            reporting_manager_id=employee_data['reporting_manager_id'],
            joining_date=employee_data['joining_date'] or timezone.now().date(),
            address_line1=employee_data['address_line1'],
            city=employee_data['city'],
            state=employee_data['state'],
            postal_code=employee_data['postal_code'],
            employment_status='active',
            created_by=self.context['request'].user if 'request' in self.context else None,
            updated_by=self.context['request'].user if 'request' in self.context else None,
        )

        # Optional: notify user
        # send_verification_email(user)

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "photo",
            "phone_number",
            "gender",
            "job_title",
            "department",
            "is_active",
            "is_verified",
            "is_first_login",
            "date_joined",
        ]

    def get_photo(self, obj):
        request = self.context.get("request")
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        # 🚨 NEVER log attrs["password"]
        print("LOGIN PAYLOAD: %s", attrs)
        logger.info("LOGIN PAYLOAD KEYS: %s", list(attrs.keys()))
        logger.info("USERNAME VALUE: %s", attrs.get("username"))
        logger.info("EMAIL VALUE: %s", attrs.get("email"))
        
        logger.info(
            "Login attempt for username=%s",
            attrs.get("username") or attrs.get("email")
        )

        data = super().validate(attrs)
        user = self.user

        print(
            "User resolved: id=%s email=%s is_active=%s is_verified=%s is_staff=%s is_first_login=%s",
            user.id,
            user.email,
            user.is_active,
            getattr(user, "is_verified", None),
            user.is_staff,
            getattr(user, "is_first_login", None),
        )

        # 🔐 Allow admins
        if user.is_staff or user.is_superuser:
            logger.info("Admin login allowed: %s", user.email)
            return data

        # 🔒 Inactive account
        if not user.is_active:
            logger.warning("Inactive login blocked: %s", user.email)
            raise AuthenticationFailed("Account is inactive. Please verify your email.")

        # 🔒 Email not verified
        if not getattr(user, "is_verified", False):
            logger.warning("Unverified email login blocked: %s", user.email)
            raise AuthenticationFailed("Email not verified. Please check your email.")

        # 👇 Send first login flag
        data["is_first_login"] = user.is_first_login

        # 👇 Flip flag
        if user.is_first_login:
            logger.info("First login detected, flipping flag for %s", user.email)
            user.is_first_login = False
            user.save(update_fields=["is_first_login"])

        logger.info("Login successful: %s", user.email)
        return data


class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "first_name", "last_name"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False          # 🔒 LOCK ACCOUNT
        user.is_verified = False
        user.save()
       
        
        send_verification_email(user)


        return user



class SetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs