import os
from django.shortcuts import render, redirect

# Create your views here.
from auth_app.emails import send_password_reset_email
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny,IsAdminUser, IsAuthenticated
from rest_framework.generics import CreateAPIView
from .serializers import AdminCreateUserSerializer, ChangePasswordSerializer, CustomTokenObtainPairSerializer
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User
from .utils import generate_password_setup_token, verify_email_token
from rest_framework import status
from .utils import verify_password_setup_token
from dotenv import load_dotenv

load_dotenv()


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

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
class SetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        token = request.data.get("token")
        password = request.data.get("password")

        user_id = verify_password_setup_token(token)

        if not user_id:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, id=user_id)
        user.set_password(password)
        user.save()

        return Response({"message": "Password set successfully"})

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

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
 
class VerifyEmailView(APIView):
    authentication_classes = []
    permission_classes = []

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

        # return Response({"message": "Email verified successfully"})
#  🚀 Redirect to frontend change-password page
        return redirect(
            f"{os.environ.get('BASE_URL_FRONTEND')}/set-password?token={pwd_token}"
        )   




class AdminCreateUserView(CreateAPIView):
    permission_classes = [IsAdminUser]  # only admin can create users
    queryset = User.objects.all()
    serializer_class = AdminCreateUserSerializer





class LoginAPI(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,)

