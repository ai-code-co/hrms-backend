from rest_framework import serializers

from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

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
       
     

        return user
