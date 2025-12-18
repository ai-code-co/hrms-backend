from django.urls import path
from .views import ChangePasswordView, ForgotPasswordView, LoginAPI, AdminCreateUserView, SetPasswordView, VerifyEmailView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', LoginAPI.as_view(), name='login'),
    path("users/", AdminCreateUserView.as_view(), name="admin-create-user"),
    path("verify-email/<str:token>/", VerifyEmailView.as_view()),
    path("set-password/", SetPasswordView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
