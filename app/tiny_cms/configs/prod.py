import os
from pathlib import Path

from . import base as _base

BASE_DIR = _base.BASE_DIR
SECRET_KEY = _base.SECRET_KEY
DEBUG = _base.DEBUG
ALLOWED_HOSTS = _base.ALLOWED_HOSTS

INSTALLED_APPS = list(_base.INSTALLED_APPS)
MIDDLEWARE = list(_base.MIDDLEWARE)

ROOT_URLCONF = _base.ROOT_URLCONF
TEMPLATES = _base.TEMPLATES
WSGI_APPLICATION = _base.WSGI_APPLICATION

DATABASES = _base.DATABASES
AUTH_PASSWORD_VALIDATORS = _base.AUTH_PASSWORD_VALIDATORS

LANGUAGE_CODE = _base.LANGUAGE_CODE
TIME_ZONE = _base.TIME_ZONE
USE_I18N = _base.USE_I18N
USE_TZ = _base.USE_TZ

STATIC_URL = _base.STATIC_URL
STATICFILES_DIRS = list(_base.STATICFILES_DIRS)
STATIC_ROOT = _base.STATIC_ROOT

DEFAULT_AUTO_FIELD = _base.DEFAULT_AUTO_FIELD

MEDIA_URL = _base.MEDIA_URL
MEDIA_ROOT = _base.MEDIA_ROOT

# Безопасность
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://dl-blog.ru",
    "https://www.dl-blog.ru",
]
# Logging Configuration
# https://docs.djangoproject.com/en/5.1/topics/logging/

# Create logs directory if it doesn't exist
LOGS_DIR = Path(os.environ.get("LOG_DIR", BASE_DIR / "logs"))
LOGS_DIR.mkdir(parents=True, exist_ok=True)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {asctime} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "console_debug": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file_django": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "django.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_errors": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "errors.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_blog": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "blog.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 3,
            "formatter": "verbose",
        },
        "file_settings": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "settings.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 3,
            "formatter": "verbose",
        },
        "file_security": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "security.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Django core loggers
        "django.request": {
            "handlers": ["file_errors", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["file_security", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        # Application loggers
        "blog": {
            "handlers": ["console", "file_blog", "file_errors"],
            "level": "ERROR",
            "propagate": False,
        },
        "settings": {
            "handlers": ["console", "file_settings", "file_errors"],
            "level": "ERROR",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file_django"],
        "level": "INFO",
    },
}
