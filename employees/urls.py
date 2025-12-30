from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet

router = DefaultRouter()
router.register(r'', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('', include(router.urls)),
]

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import (
#     EmployeeViewSet,
#     EmergencyContactViewSet,
#     EducationViewSet,
#     WorkHistoryViewSet
# )

# router = DefaultRouter()
# router.register(r'', EmployeeViewSet, basename='employee')
# router.register(r'emergency-contacts', EmergencyContactViewSet, basename='emergency-contact')
# router.register(r'educations', EducationViewSet, basename='education')
# router.register(r'work-histories', WorkHistoryViewSet, basename='work-history')

# urlpatterns = [
#     path('', include(router.urls)),
# ]