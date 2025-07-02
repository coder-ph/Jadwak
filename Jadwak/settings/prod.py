"""production environ settings."""

import os

from .base import BASE_DIR, env

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts in production (your domain names)
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS", default=["yourdomain.com", "www.yourdomain.com"]
)

# Security settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env.bool(
    "DJANGO_SECURE_SSL_REDIRECT", default=True
)  # Ensure HTTPS
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # Required if behind Nginx/load balancer

# CORS settings for production (restrict to your frontend domain)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list(
    "DJANGO_CORS_ALLOWED_ORIGINS", default=["https://yourfrontend.com"]
)

# Static and media files in production (S3 or similar)
# Install django-storages and boto3 for AWS S3
# pip install django-storages boto3
# INSTALLED_APPS += ['storages']

# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
# AWS_S3_CUSTOM_DOMAIN = env('AWS_S3_CUSTOM_DOMAIN', default=f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com') # Optional

# Logging (configure for production monitoring)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/jenga.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        # Add Sentry, CloudWatch, etc., handlers here
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "jenga_platform": {  # Your project-specific logger
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        # Add other loggers for your apps
    },
}

# Email backend for production (e.g., SendGrid, Mailgun, AWS SES)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@yourdomain.com")

# Celery in production (use different Redis DB or separate Redis instance)
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL_PROD", default="redis://your_prod_redis_host:6379/1"
)  # Example: use DB 1
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND_PROD", default="redis://your_prod_redis_host:6379/1"
)
