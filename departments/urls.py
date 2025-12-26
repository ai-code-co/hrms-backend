from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, DesignationViewSet

router = DefaultRouter()
router.register(r'', DepartmentViewSet, basename='department')
router.register(r'designations', DesignationViewSet, basename='designation')

urlpatterns = [
    path('', include(router.urls)),
]

