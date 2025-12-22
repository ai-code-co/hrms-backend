from django.urls import path
from .views import UserSalaryInfoView, GenericConfigurationView

urlpatterns = [
    path('user-salary-info/', UserSalaryInfoView.as_view(), name='user-salary-info'),
    path('generic-configuration/', GenericConfigurationView.as_view(), name='generic-configuration'),
]
