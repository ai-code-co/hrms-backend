from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import CreateAPIView
from .serializers import AdminCreateUserSerializer
from .models import User

class AdminCreateUserView(CreateAPIView):
    permission_classes = [IsAdminUser]  # only admin can create users
    queryset = User.objects.all()
    serializer_class = AdminCreateUserSerializer


class LoginAPI(TokenObtainPairView):
    permission_classes = (AllowAny,)