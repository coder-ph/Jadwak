"""admin for detection app."""

from django.contrib.gis import admin
from .models import Detection, ChangeLog


@admin.register(Detection)
class DetectionAdmin(admin.GISModelAdmin):
    """Admin interface for the Detection model."""

    list_display = (
        "satellite_image",
        "detected_class",
        "confidence",
        "location",
        "timestamp",
    )
    list_filter = ("detected_class", "timestamp", "satellite_image__site")
    search_fields = ("satellite_image__name", "detected_class", "metadata__id")
    raw_id_fields = ("satellite_image",)
    default_lon = 36.817223
    default_lat = -1.286389
    default_zoom = 12


@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    """changelog admin interface."""

    # ModelAdmin is fine as ChangeLog doesn't have spatial fields directly
    list_display = ("site", "change_type", "image_before", "image_after", "timestamp")
    list_filter = ("change_type", "site", "timestamp")
    search_fields = ("site__name", "description", "change_type")
    raw_id_fields = (
        "site",
        "image_before",
        "image_after",
    )  # Use raw ID for ForeignKey fields
    readonly_fields = ("timestamp",)
