from rest_framework import serializers

from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from .emails import send_verification_email


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # 🔐 Allow admins to login without verification
        if user.is_staff or user.is_superuser:
            return data


        # 🔒 Block if account is inactive
        if not user.is_active:
            raise AuthenticationFailed("Account is inactive. Please verify your email.")

        # 🔒 Block if email not verified
        if not getattr(user, "is_verified", False):
            raise AuthenticationFailed("Email not verified. Please check your email.")
        
        # 👇 SEND FIRST LOGIN FLAG
        data["is_first_login"] = user.is_first_login

        # 👇 AFTER FIRST LOGIN, FLIP FLAG
        if user.is_first_login:
            user.is_first_login = False
            user.save(update_fields=["is_first_login"])

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
    password = serializers.CharField(min_length=8)



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs