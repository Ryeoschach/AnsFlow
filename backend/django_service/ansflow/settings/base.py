"""
Django base settings for AnsFlow CI/CD platform.

This file contains base settings shared across all environments.
Environment-specific settings should be placed in separate files.
"""

import os
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env file
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=[
    'localhost', 
    '127.0.0.1', 
    'testserver',
    'host.docker.internal',  # 允许 Docker 内部访问
    '0.0.0.0',  # 允许所有主机访问（开发环境）
    'django_service',  # Docker 容器名
    'ansflow_django',  # Docker 容器名
])


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'django_prometheus',
    'django_extensions',
    'channels',
]

LOCAL_APPS = [
    'monitoring',
    'pipelines',
    'project_management', 
    'user_management',
    'workflow',
    'audit',
    'cicd_integrations',
    'realtime',
    'analytics',
    'ansible_integration',
    'docker_integration',
    'kubernetes_integration',
    'settings_management',
    'logging_system',  # 统一日志系统
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'monitoring.prometheus.MetricsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.LoggingMiddleware',  # AnsFlow统一日志中间件
    'monitoring.integration.MetricsLoggingMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'ansflow.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ansflow.wsgi.application'

# ASGI application for WebSocket support
ASGI_APPLICATION = 'ansflow.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', default='ansflow'),
        'USER': env('DB_USER', default='root'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 排除特定端点的认证要求
    'UNAUTHENTICATED_USER': 'django.contrib.auth.models.AnonymousUser',
}

# DRF Spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'AnsFlow CI/CD Platform API',
    'DESCRIPTION': 'API documentation for AnsFlow CI/CD platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# CORS settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
]

# Celery Configuration - 迁移到RabbitMQ
CELERY_BROKER_URL = env(
    'CELERY_BROKER_URL', 
    default='amqp://ansflow:ansflow_rabbitmq_123@localhost:5672/ansflow_vhost'
)
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/6')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# RabbitMQ 路由和队列配置
CELERY_TASK_ROUTES = {
    # 高优先级任务队列
    'cicd_integrations.tasks.execute_pipeline': {'queue': 'high_priority'},
    'cicd_integrations.tasks.execute_workflow': {'queue': 'high_priority'},
    
    # 中等优先级任务队列
    'cicd_integrations.tasks.generate_execution_reports': {'queue': 'medium_priority'},
    'cicd_integrations.tasks.health_check_tools': {'queue': 'medium_priority'},
    'cicd_integrations.tasks.monitor_long_running_executions': {'queue': 'medium_priority'},
    
    # 低优先级任务队列
    'cicd_integrations.tasks.cleanup_old_executions': {'queue': 'low_priority'},
    'cicd_integrations.tasks.backup_pipeline_configurations': {'queue': 'low_priority'},
    'audit.tasks.cleanup_old_logs': {'queue': 'low_priority'},
}

# 队列配置
CELERY_TASK_DEFAULT_QUEUE = 'medium_priority'
CELERY_TASK_QUEUES = {
    'high_priority': {
        'exchange': 'high_priority',
        'exchange_type': 'direct',
        'routing_key': 'high_priority',
    },
    'medium_priority': {
        'exchange': 'medium_priority',
        'exchange_type': 'direct',
        'routing_key': 'medium_priority',
    },
    'low_priority': {
        'exchange': 'low_priority',
        'exchange_type': 'direct',
        'routing_key': 'low_priority',
    },
}

# Celery 性能优化配置
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # 防止任务积压
CELERY_TASK_ACKS_LATE = True  # 任务完成后确认
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_TASK_COMPRESSION = 'gzip'  # 压缩任务数据
CELERY_RESULT_COMPRESSION = 'gzip'

# 任务执行配置
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5分钟软限制
CELERY_TASK_TIME_LIMIT = 600  # 10分钟硬限制
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 重试间隔60秒

# Beat调度器配置
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Redis Cache Configuration - 多数据库优化配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'ansflow:default',
        'VERSION': 1,
        'TIMEOUT': 300,  # 5 minutes default timeout
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_SESSION_URL', default='redis://127.0.0.1:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'ansflow:session',
        'VERSION': 1,
        'TIMEOUT': 86400,  # 24 hours for sessions
    },
    'api': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_API_URL', default='redis://127.0.0.1:6379/4'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 80,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'ansflow:api',
        'VERSION': 1,
        'TIMEOUT': 600,  # 10 minutes for API responses
    },
    'pipeline': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_PIPELINE_URL', default='redis://127.0.0.1:6379/5'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 60,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'ansflow:pipeline',
        'VERSION': 1,
        'TIMEOUT': 1800,  # 30 minutes for pipeline data
    }
}

# Session configuration - 临时使用数据库Session确保稳定性
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24小时
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG  # 生产环境使用HTTPS

# 注意：Redis会话配置暂时注释，等确认django-redis包正常后再启用
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'session'

# Channels configuration - WebSocket using dedicated Redis database
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_CHANNELS_URL', default='redis://127.0.0.1:6379/2')],
            'capacity': 1500,  # 默认通道容量
            'expiry': 60,  # 消息过期时间（秒）
        },
    },
}

# Logging configuration
# 使用AnsFlow统一日志配置
import sys
from pathlib import Path

# 添加common模块到Python路径
common_path = BASE_DIR / 'common'
if common_path.exists() and str(common_path) not in sys.path:
    sys.path.insert(0, str(common_path))

try:
    from common.logging_config import AnsFlowLoggingConfig
    
    # 创建AnsFlow统一日志配置实例并设置
    logging_config = AnsFlowLoggingConfig()
    logging_config.setup_logging()
    
    # Django的LOGGING配置（保持兼容性）
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'ansflow_json': {
                '()': 'common.logging_config.AnsFlowJSONFormatter',
            },
            'simple': {
                'format': '{levelname} {asctime} {name} {message}',
                'style': '{',
            },
        },
        'filters': {
            'sensitive_data': {
                '()': 'common.logging_config.SensitiveDataFilter',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'filters': ['sensitive_data'],
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': BASE_DIR.parent.parent / 'logs' / 'django.log',  # 修正为项目根目录
                'when': 'midnight',
                'interval': 1,
                'backupCount': 30,
                'formatter': 'ansflow_json',
                'filters': ['sensitive_data'],
            },
            # 暂时注释掉redis处理器，避免配置错误
            'redis': {
                'level': 'INFO',  
                '()': 'common.logging_config.RedisLogHandler',
                'stream_name': 'ansflow:logs:stream',
                'max_len': 10000,
                'formatter': 'ansflow_json',
                'filters': ['sensitive_data'],
            },
        },
        'root': {
            'handlers': ['console', 'file'] + (['redis'] if env.bool('LOGGING_ENABLE_REDIS', default=False) else []),
            'level': env('LOG_LEVEL', default='INFO'),
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'] + (['redis'] if env.bool('LOGGING_ENABLE_REDIS', default=False) else []),
                'level': 'INFO',
                'propagate': False,
            },
            'ansflow': {
                'handlers': ['console', 'file'] + (['redis'] if env.bool('LOGGING_ENABLE_REDIS', default=False) else []),
                'level': env('LOG_LEVEL', default='DEBUG'),
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'file'] + (['redis'] if env.bool('LOGGING_ENABLE_REDIS', default=False) else []),
                'level': 'INFO',
                'propagate': False,
            },
            'django.security': {
                'handlers': ['console', 'file'] + (['redis'] if env.bool('LOGGING_ENABLE_REDIS', default=False) else []),
                'level': 'WARNING',
                'propagate': False,
            },
        },
    }
    
except ImportError:
    # 如果AnsFlowLoggingConfig不可用，使用默认配置
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': BASE_DIR / 'logs' / 'django.log',
                'when': 'midnight',
                'interval': 1,
                'backupCount': 30,
                'formatter': 'verbose',
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'ansflow': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# URL配置
APPEND_SLASH = False  # 禁用自动添加斜杠，避免POST请求重定向问题

# 加密配置
ENCRYPTION_KEY = env('ENCRYPTION_KEY', default='K8x6P7_q5mZtTrI1xvU2oN4YzW9eV3jA0lDcE8nRfQg=')
