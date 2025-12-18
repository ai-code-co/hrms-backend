from django.urls import path
from .views import ChangePasswordView, ForgotPasswordView, LoginAPI, AdminCreateUserView, SetPasswordView, VerifyEmailView


urlpatterns = [
    path('login/', LoginAPI.as_view(), name='login'),
    path("users/", AdminCreateUserView.as_view(), name="admin-create-user"),
    path("verify-email/<str:token>/", VerifyEmailView.as_view()),
    path("set-password/", SetPasswordView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
]
