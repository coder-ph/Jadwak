"""Jadwak development environment."""
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
DATABASES = {
    "default": env.db_url(default="postgis://user:password@localhost:5432/jadwak_dev"),
}

CORS_ALLOWED_ORIGINS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
