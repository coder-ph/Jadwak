"""Jadwak development environment."""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]


CORS_ALLOWED_ORIGINS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
