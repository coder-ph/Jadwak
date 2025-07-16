"""This module contains the configuration for the Alerts application."""
from django.apps import AppConfig


class AlertsConfig(AppConfig):
    """Configuration class for the Alerts application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "alerts"
