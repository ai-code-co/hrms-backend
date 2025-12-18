from django.urls import path
from .views import LoginAPI, AdminCreateUserView, VerifyEmailView


urlpatterns = [
    path('login/', LoginAPI.as_view(), name='login'),
    path("users/", AdminCreateUserView.as_view(), name="admin-create-user"),
    path("verify-email/<str:token>/", VerifyEmailView.as_view()),
]
