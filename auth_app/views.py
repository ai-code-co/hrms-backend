"""
views.py

This file defines all authentication-related APIs.
Each endpoint is designed with:
- minimal data exposure
- clear security boundaries
- frontend-friendly flows
"""
import os
from django.shortcuts import render, redirect
# Create your views here.
from auth_app.emails import send_password_reset_email
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny,IsAdminUser, IsAuthenticated
from rest_framework.generics import CreateAPIView
from .serializers import AdminCreateUserSerializer, ChangePasswordSerializer, CustomTokenObtainPairSerializer, SetPasswordSerializer
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from .models import User
from .utils import generate_password_setup_token, verify_email_token
from rest_framework import status
from .utils import verify_password_setup_token
from rest_framework_simplejwt.views import TokenRefreshView
from dotenv import load_dotenv
from .serializers import UserProfileSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

load_dotenv()

# ------------------------------------------------------------------
# User profile creation
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# User profile
# ------------------------------------------------------------------

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get the profile of the currently logged-in user.",
        responses={200: UserProfileSerializer()}
    )
    def get(self, request):
        serializer = UserProfileSerializer(
            request.user,
            context={"request": request}
        )
        return Response(serializer.data)


# ------------------------------------------------------------------
# FORGOT PASSWORD
# ------------------------------------------------------------------

class ForgotPasswordView(APIView):
    """
    Initiates password reset via email.

    Security:
    - Always returns success message
    - Does NOT reveal if email exists
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Initiate password reset process by sending an email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='User email address'),
            },
            required=['email']
        ),
        responses={200: openapi.Response("Reset email sent if account exists")}
    )
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required"}, status=400)

        user = User.objects.filter(email=email).first()

        # 🔐 IMPORTANT: do NOT reveal if user exists
        if user:
            send_password_reset_email(user)

        return Response({
            "message": "If an account exists, a password reset link has been sent."
        })


# ------------------------------------------------------------------
# SET PASSWORD (First login OR reset)
# ------------------------------------------------------------------




class SetPasswordView(APIView):
    """
    Sets password using a secure token.

    Used for:
    - first-time password setup
    - forgot-password reset
    """
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Set new password using a secure token.",
        request_body=SetPasswordSerializer,
        responses={200: openapi.Response("Password updated successfully")}
    )
    def post(self, request):
        print("🔵 STEP 1: Entered SetPasswordView")

        print("🔵 STEP 2: Raw request.data =", request.data)

        token = request.data.get("token")
        # password = request.data.get("password")
        password = request.data.get("new_password")

        print("🔵 STEP 3: token =", token)
        print("🔵 STEP 4: raw password repr =", repr(password))

        user_id = verify_password_setup_token(token)

        print("🔵 STEP 5: user_id from token =", user_id)

        if not user_id:
            print("🔴 ERROR: Token invalid or expired")
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, id=user_id)

        print("🔵 STEP 6: User fetched")
        print("   username =", user.username)
        print("   email =", user.email)
        print("   is_active (before) =", user.is_active)
        print("   is_verified (before) =", getattr(user, "is_verified", None))

        user.set_password(password)
        print("🔵 STEP 7: Password set using set_password()")

        user.is_active = True
        user.is_verified = True

        print("🔵 STEP 8: Flags updated")
        print("   is_active (after) =", user.is_active)
        print("   is_verified (after) =", user.is_verified)

        user.save()
        print("🔵 STEP 9: User saved to database")

        # 🔥 CRITICAL VERIFICATION
        password_check = user.check_password(password)
        print("🔵 STEP 10: check_password result =", password_check, password)

        if not password_check:
            print("🚨 CRITICAL BUG: Password saved does NOT match input!")

        print("🟢 STEP 11: SetPasswordView completed successfully")

        return Response({"message": "Password set successfully"})


# ------------------------------------------------------------------
# CHANGE PASSWORD (Logged-in user)
# ------------------------------------------------------------------

class ChangePasswordView(APIView):
    """
    Allows authenticated users to change password.

    Requires:
    - old password verification
    - JWT authentication
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change internal user password.",
        request_body=ChangePasswordSerializer,
        responses={200: openapi.Response("Password changed successfully")}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password changed successfully. Please login again."}
        )
# ------------------------------------------------------------------
# EMAIL VERIFICATION
# ------------------------------------------------------------------

"""
    Verifies email ownership.

    On success:
    - activates account
    - marks email verified
    - generates password setup token
    - redirects user to frontend set-password page
    """
class VerifyEmailView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Verify user email using a token.",
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_PATH, type=openapi.TYPE_STRING, description='Verification token')
        ],
        responses={302: openapi.Response("Redirects to set-password page")}
    )
    def get(self, request, token):
        user_id = verify_email_token(token)

        if not user_id:
            return Response(
                {"error": "Invalid or expired verification link"},
                status=400
            )

        user = get_object_or_404(User, id=user_id)
        user.is_active = True
        user.is_verified = True
        user.save()

          # 🔐 Generate password setup token
        pwd_token = generate_password_setup_token(user.id)

#  🚀 Redirect to frontend change-password page
        return redirect(
            f"{os.environ.get('BASE_URL_FRONTEND')}/set-password?token={pwd_token}"
        )   


# ------------------------------------------------------------------
# ADMIN CREATES USER
# ------------------------------------------------------------------

"""
    Allows ONLY admin users to create accounts.

    Flow:
    Admin creates user
    → User inactive + unverified
    → Verification email sent
    """
class AdminCreateUserView(CreateAPIView):
    permission_classes = [IsAdminUser]  # only admin can create users
    queryset = User.objects.all()
    serializer_class = AdminCreateUserSerializer



# ------------------------------------------------------------------
# LOGIN (JWT)
# ------------------------------------------------------------------
"""
    Issues JWT tokens.

    Custom serializer ensures:
    - email verified
    - account active
    - admins bypass verification
    """

class LoginAPI(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
 


# ------------------------------------------------------------------
# LOGOUT (Blacklist Token)
# ------------------------------------------------------------------

class LogoutView(APIView):
    """
    Standard Logout API.
    Supports two modes:
    Option A: Logout from current device only (Requires refresh token).
    Option B: Logout from all devices (Stateless, no body required).
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Log out user (Option B currently active: Logs out from ALL devices).",
        responses={
            205: openapi.Response("Logout successful"),
            400: openapi.Response("Logout failed")
        }
    )
    def post(self, request):
        # ---------------------------------------------------------
        # OPTION A: Logout from single device (Requires 'refresh' token in body)
        # ---------------------------------------------------------
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        # ---------------------------------------------------------
        # OPTION B: Logout from all devices (Nuclear Logout)
        # ---------------------------------------------------------
        # try:
        #     tokens = OutstandingToken.objects.filter(user=request.user)
        #     for token in tokens:
        #         BlacklistedToken.objects.get_or_create(token=token)

        #     return Response(
        #         {"message": "Logged out successfully from all devices."}, 
        #         status=status.HTTP_205_RESET_CONTENT
        #     )
        # except Exception as e:
        #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


