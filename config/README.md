# Configuration (config) ⚙️

## What is this?

The **config** directory contains Django project settings and URL routing:
- `settings.py` - All project configuration
- `urls.py` - Main URL routing
- `wsgi.py` - WSGI server configuration
- `asgi.py` - ASGI server configuration

## Why do we need it?

- **Centralized Settings** - One place for all configuration
- **Environment Management** - Different settings for dev/prod
- **URL Routing** - Map URLs to app endpoints
- **Security** - Manage secret keys and security settings

## Key Files

### settings.py

Main configuration file containing:

#### Database Configuration
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hrms_db',
        'USER': 'hrms_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

#### Installed Apps
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    # Custom apps
    'auth_app',
    'employees',
    'departments',
    'leaves',
    'holidays',
    'inventory',
]
```

#### JWT Configuration
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

#### CORS Settings
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend.com",
]
```

#### Email Configuration
```python
EMAIL_BACKEND = 'anymail.backends.sendinblue.EmailBackend'
ANYMAIL = {
    "SENDINBLUE_API_KEY": os.environ.get('MAILGUN_API_KEY'),
}
```

### urls.py

Main URL configuration:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.urls')),
    path('api/employees/', include('employees.urls')),
    path('api/departments/', include('departments.urls')),
    path('api/leaves/', include('leaves.urls')),
    path('api/holidays/', include('holidays.urls')),
    path('api/inventory/', include('inventory.urls')),
    
    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger')),
    path('redoc/', schema_view.with_ui('redoc')),
]
```

## Environment Variables

Required in `.env` file:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=hrms_db
DB_USER=hrms_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# For production (Render/TiDB)
DATABASE_URL=mysql://user:pass@host:port/db

# Email
MAILGUN_API_KEY=your-mailgun-key

# Frontend
BASE_URL_FRONTEND=http://localhost:3000

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOW_CREDENTIALS=True
```

## Security Settings

### Production Settings
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Development Settings
```python
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

## Middleware

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files
    'corsheaders.middleware.CorsMiddleware',  # CORS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## Static Files

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

## API Documentation

Swagger UI available at:
- `/swagger/` - Interactive API documentation
- `/redoc/` - Alternative documentation format

## Deployment

### Local Development
```bash
python manage.py runserver
```

### Production (Render)
Uses `Procfile`:
```
web: python manage.py migrate && gunicorn config.wsgi:application
```

## Summary

The config directory is the heart of the Django project, managing all settings, routing, and deployment configuration! ⚙️
