"""This module contains serializers for the Alert and AlertRule models."""

from rest_framework import serializers
from .models import Alert, AlertRule


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for the Alert model."""

    site_name = serializers.ReadOnlyField(source="site.name")

    user_username = serializers.ReadOnlyField(source="user.username", default=None)
    change_log_id = serializers.ReadOnlyField(source="change_log.id", default=None)

    class Meta:
        """Meta options for the AlertSerializer."""

        model = Alert
        fields = (
            "id",
            "type",
            "site",
            "site_name",
            "user",
            "user_username",
            "triggered_on",
            "status",
            "description",
            "change_log",
            "change_log_id",
            "metadata",
        )
        read_only_fields = ("triggered_on", "user", "change_log", "metadata")


class AlertRuleSerializer(serializers.ModelSerializer):
    """Serializer for the AlertRule model."""

    site_name = serializers.ReadOnlyField(source="site.name")

    class Meta:
        """Meta options for the AlertRuleSerializer."""

        model = AlertRule
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")
