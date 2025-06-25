"""
Development settings for AnsFlow CI/CD platform.
"""
import environ
from .base import *

# Initialize environment for development
env = environ.Env()

# Debug settings - Override base settings
DEBUG = True

# Development hosts - Override base settings
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database for development (MySQL)
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': env('DB_NAME', default='ansflow_db'),
        'USER': env('DB_USER', default='ansflow_user'),
        'PASSWORD': env('DB_PASSWORD', default='ansflow_password_123'),
        'HOST': env('DB_HOST', default='127.0.0.1'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Add development-specific apps (removed debug_toolbar for now)
DEVELOPMENT_APPS = [
    # 'debug_toolbar',  # Temporarily disabled
]

INSTALLED_APPS = INSTALLED_APPS + DEVELOPMENT_APPS

# Add development middleware (removed debug_toolbar for now)
DEVELOPMENT_MIDDLEWARE = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # Temporarily disabled
]

MIDDLEWARE = DEVELOPMENT_MIDDLEWARE + MIDDLEWARE

# Debug Toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Disable cache in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging level for development
import logging
logging.basicConfig(level=logging.DEBUG)
