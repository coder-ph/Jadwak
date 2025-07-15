"""apps.py for the detection application."""
from django.apps import AppConfig


class DetectionConfig(AppConfig):
    """Configuration for the detection app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "detection"
