from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceTypeViewSet,
    DeviceViewSet,
    InventoryDashboardView
)

router = DefaultRouter()
router.register(r'device-types', DeviceTypeViewSet, basename='device-type')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'inventory', InventoryDashboardView, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
]

