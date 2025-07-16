"""alerts."""
from django.db import models
from django.conf import settings


from core.models import Site
from detection.models import ChangeLog

# Create your models here.


class Alert(models.Model):
    """Represents a triggered alert for a specific event on site."""

    ALERT_TYPE_CHOICE = [
        ("EQUIPMENT_MISSING", "Equipment Missing"),
        ("NEW_EQUIPMENT_DETECTED", "New Equipment Detected"),
        ("COUNT_THRESHOLD_EXCEEDED", "Detection Count Threshold Exceeded"),
        ("SITE_ACTIVITY_HIGH", "High Site Activity"),
        ("SITE_ACTIVITY_LOW", "Low Site Activity"),
        ("IMAGE_FETCH_FAILED", "Image Fetch Failed"),
        ("AI_PROCESSING_ERROR", "AI Processing Error"),
        ("OTHER", "Other Alert"),
    ]

    ALERT_STATUS_CHOICES = [
        ("UNREAD", "Unread"),
        ("READ", "Read"),
        ("RESOLVED", "Resolved"),
    ]

    type = models.CharField(
        max_length=50, choices=ALERT_TYPE_CHOICE, help_text="type of alert triggered"
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="The site where the alert was triggered",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        help_text="Optional: User who received this alert (if user-specific)",
    )

    triggered_on = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the alert was created"
    )

    status = models.CharField(
        max_length=20,
        choices=ALERT_STATUS_CHOICES,
        default="UNREAD",
        help_text="Current status of the alert",
    )

    description = models.TextField(
        blank=True, help_text="A human-readable summary of the alert"
    )

    change_log = models.ForeignKey(
        ChangeLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        help_text="Optional: The ChangeLog entry that triggered this alert",
    )

    metadata = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Detailed JSON data about the alert context",
    )

    class Meta:
        """Meta options for the Alert model."""

        verbose_name = "Alert"
        verbose_name_plural = "Alerts"
        ordering = ["-triggered_on"]

    def __str__(self: "Alert") -> str:
        """Return string representation of the Alert model."""
        return f"Alert: {self.get_type_display()} on {self.site.name} ({self.status})"


class AlertRule(models.Model):
    """Defines configurable rules that automatically trigger alerts."""

    RULE_TYPE_CHOICES = [
        ("EQUIPMENT_MISSING", "Equipment Missing Detection"),
        ("NEW_EQUIPMENT", "New Equipment Detected"),
        ("COUNT_THRESHOLD", "Detection Count Threshold"),
        ("ACTIVITY_LEVEL", "Site Activity Level"),
        ("IMAGE_FAILURE", "Image Processing Failure"),
        ("NO_DATA_PERIOD", "No New Data for Period"),
    ]

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="alert_rules",
        help_text="The site this rule applies to",
    )
    rule_type = models.CharField(
        max_length=50, choices=RULE_TYPE_CHOICES, help_text="Type of alert rule"
    )

    threshold = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Threshold value for the rule (e.g., '10', 'HIGH')",
    )

    target_class = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Optional: Target equipment class for specific rules",
    )

    is_active = models.BooleanField(
        default=True, help_text="Whether this alert rule is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the AlertRule model."""

        verbose_name = "Alert Rule"
        verbose_name_plural = "Alert Rules"
        unique_together = ("site", "rule_type", "target_class")
        ordering = ["site", "rule_type"]

    def __str__(self: "AlertRule") -> str:
        """Return string representation of the AlertRule model."""
        return f"Rule: {self.get_rule_type_display()} for {self.site.name} (Active: {self.is_active})"
