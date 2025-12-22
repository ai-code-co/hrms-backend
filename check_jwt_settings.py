#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import timedelta
from rest_framework_simplejwt.settings import api_settings
from django.conf import settings

print("=" * 60)
print("JWT TOKEN CONFIGURATION")
print("=" * 60)

# Check if SIMPLE_JWT is configured
if hasattr(settings, 'SIMPLE_JWT'):
    print("\n✅ Custom SIMPLE_JWT settings found:")
    for key, value in settings.SIMPLE_JWT.items():
        print(f"  {key}: {value}")
else:
    print("\n⚠️  No custom SIMPLE_JWT settings found")
    print("  Using default settings from rest_framework_simplejwt")

print("\n📋 Current JWT Settings:")
print(f"  Access Token Lifetime: {api_settings.ACCESS_TOKEN_LIFETIME}")
print(f"  Refresh Token Lifetime: {api_settings.REFRESH_TOKEN_LIFETIME}")
print(f"  Rotate Refresh Tokens: {api_settings.ROTATE_REFRESH_TOKENS}")
print(f"  Blacklist After Rotation: {api_settings.BLACKLIST_AFTER_ROTATION}")
print(f"  Algorithm: {api_settings.ALGORITHM}")

print("\n⏰ Token Expiry Times:")
print(f"  Access Token expires in: {api_settings.ACCESS_TOKEN_LIFETIME.total_seconds() / 60} minutes")
print(f"  Refresh Token expires in: {api_settings.REFRESH_TOKEN_LIFETIME.total_seconds() / 3600 / 24} days")

print("\n" + "=" * 60)
