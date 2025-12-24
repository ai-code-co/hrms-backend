"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="HRMS API",
        default_version='v1',
        description="API documentation for Human Resource Management System",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@hrms.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

from config.views import TableDataView

urlpatterns = [
    path('api/slack/interactions/', include('notifications.urls')),
    path('slack/interactions/', include('notifications.urls')), # Root fallback
    path('jet/', include('jet.urls', 'jet')),  
    path('admin/', admin.site.urls),
    path("auth/", include("auth_app.urls")),
    path("api/", include("departments.urls")),
    path("api/", include("employees.urls")),
    path("table-data/", TableDataView.as_view()),
    path("api/", include("holidays.urls")),
    path("api/", include("inventory.urls")),
    path('api/leaves/', include('leaves.urls')),
    path('api/', include('attendance.urls')),
    path('api/payroll/', include('payroll.urls')),
    # path('api/', include('notifications.urls')), # Removed from here
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
