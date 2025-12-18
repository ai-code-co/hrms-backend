from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny,IsAdminUser
from rest_framework.generics import CreateAPIView
from .serializers import AdminCreateUserSerializer, CustomTokenObtainPairSerializer
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User
from .utils import verify_email_token

class AdminCreateUserView(CreateAPIView):
    permission_classes = [IsAdminUser]  # only admin can create users
    queryset = User.objects.all()
    serializer_class = AdminCreateUserSerializer


class LoginAPI(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,)



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

        return Response({"message": "Email verified successfully"})