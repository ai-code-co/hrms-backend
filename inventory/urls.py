from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceTypeViewSet,
    DeviceViewSet,
    InventoryDashboardViewSet
)

router = DefaultRouter()
router.register(r'device-types', DeviceTypeViewSet, basename='device-type')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'', InventoryDashboardViewSet, basename='inventory-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
