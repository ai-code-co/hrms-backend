from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveViewSet

router = DefaultRouter()
router.register(r'', LeaveViewSet, basename='leaves')

urlpatterns = [
    path('', include(router.urls)),
]
