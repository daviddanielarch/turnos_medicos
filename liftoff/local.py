"""
Local development settings for Fer App
This file contains settings specific to local development environment
"""

import os

# Database configuration for local development with Docker Compose
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "liftoff",
        "USER": "pguser",
        "PASSWORD": "pgpassword",
        "HOST": "localhost",
        "PORT": "5433",
    }
}

# Redis configuration for local development
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Debug settings for local development
DEBUG = True

# Allow all hosts for local development
ALLOWED_HOSTS = ["*"]

# Static files configuration for local development
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "staticfiles")
STATICFILES_DIRS = [os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")]

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")

# Logging configuration for local development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

DEBUG = True
TELEGRAM_TOKEN = "5019271043:AAFs25krUpwUJbdkNvYNRykWAMS6tuhEnY0"
TELEGRAM_CHAT_ID = 658553143
