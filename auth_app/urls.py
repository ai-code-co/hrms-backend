from django.urls import path
from .views import ChangePasswordView, ForgotPasswordView, LoginAPI, AdminCreateUserView, SetPasswordView, UserProfileView, VerifyEmailView
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('login/', LoginAPI.as_view(), name='login'),
    path('login', LoginAPI.as_view()),
    path("users/", AdminCreateUserView.as_view(), name="admin-create-user"),
    path("verify-email/<str:token>/", VerifyEmailView.as_view()),
    path("set-password/", SetPasswordView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", UserProfileView.as_view(), name="user-profile"),
    path("create-user/", AdminCreateUserView.as_view(), name="admin-create-user"),
   
]

# ✅ THIS MUST BE OUTSIDE THE LIST
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )