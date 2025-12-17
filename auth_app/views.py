from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny

class LoginAPI(TokenObtainPairView):
    permission_classes = (AllowAny,)
