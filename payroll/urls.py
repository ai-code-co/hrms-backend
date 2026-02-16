from django.urls import path
from .views import UserSalaryInfoView, GenericConfigurationView, SalaryStructureAdminUpdateView

urlpatterns = [
    path('user-salary-info/', UserSalaryInfoView.as_view(), name='user-salary-info'),
    path('salary-structure/<str:identifier>/update/', SalaryStructureAdminUpdateView.as_view(), name='salary-structure-admin-update'),
    path('generic-configuration/', GenericConfigurationView.as_view(), name='generic-configuration'),
]
