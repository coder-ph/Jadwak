"""models for the detection app."""
from django.contrib.gis.db import models

# from django.utils import timezone # Removed: F401 unused import
from core.models import SatelliteImage, Site


# Create your models here.
class Detection(models.Model):
    """Model representing a detection made on a satellite image."""

    satellite_image = models.ForeignKey(
        SatelliteImage,
        on_delete=models.CASCADE,
        related_name="detections",
        help_text="The satellite image on which the detection was made.",
    )

    detected_class = models.CharField(
        max_length=100,
        help_text="The class of the detected object (e.g., 'building', 'road').",
    )

    confidence = models.FloatField(
        help_text="Confidence score of the detection, between 0 and 1."
    )

    location = models.PointField(
        srid=4326, help_text="Geospatial location of the detection (WGS84)."
    )

    timestamp = models.DateTimeField(
        auto_created=True, help_text="Timestamp when the detection was made."
    )

    metadata = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Flexible JSON for additional detection-specific data.",
    )

    class Meta:
        """Meta options for the Detection model."""

        verbose_name = "Detection"
        verbose_name_plural = "Detections"
        ordering = ["-timestamp"]

    def __str__(self: "Detection") -> str:
        """Return string representation of the Detection model."""
        return f"{self.detected_class} detected at {self.location} with confidence {self.confidence}"


class ChangeLog(models.Model):
    """Records detected changes on a site over time.

    Based on satellite imagery analysis.
    """

    CHANGE_TYPE_CHOICES = [
        ("NEW_DETECTIONS", "New Detections Found"),
        ("REMOVED_DETECTIONS", "Detections Removed"),
        ("COUNT_CHANGED", "Detection Count Changed"),
        (
            "NO_CHANGE",
            "No Significant Change",
        ),  # For reporting if a comparison was done but no major change
        ("SITE_ACTIVITY_HIGH", "High Site Activity (Mock)"),
        ("SITE_ACTIVITY_LOW", "Low Site Activity (Mock)"),
        ("OTHER", "Other Change"),
    ]

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="change_logs",
        help_text="The site where the change was detected",
    )
    image_before = models.ForeignKey(
        SatelliteImage,
        on_delete=models.SET_NULL,  # Don't delete change log if image is removed
        null=True,
        blank=True,
        related_name="changes_as_before",
        help_text="The older satellite image used for comparison",
    )
    image_after = models.ForeignKey(
        SatelliteImage,
        on_delete=models.SET_NULL,  # Don't delete change log if image is removed
        null=True,
        blank=True,
        related_name="changes_as_after",
        help_text="The newer satellite image used for comparison",
    )
    change_type = models.CharField(
        max_length=50, choices=CHANGE_TYPE_CHOICES, help_text="Type of change detected"
    )
    description = models.TextField(
        blank=True, help_text="A human-readable description of the detected change"
    )
    # Store detailed data about the change (e.g., IDs of new/removed objects)
    metadata = models.JSONField(  # <--- Use models.JSONField directly
        blank=True,
        null=True,
        default=dict,
        help_text="Detailed JSON data about the change (e.g., detection IDs, counts)",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="When this change log record was created"
    )

    class Meta:
        """Meta options for the ChangeLog model."""

        verbose_name = "Change Log"
        verbose_name_plural = "Change Logs"
        ordering = ["-timestamp"]  # Order by most recent change

    def __str__(self: "ChangeLog") -> str:
        """Return string representation of the ChangeLog model."""
        return (
            f"Change '{self.get_change_type_display()}' on {self.site.name} "
            f"at {self.timestamp.date()}"
        )
