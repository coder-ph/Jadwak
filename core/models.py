"""models module for core app."""

# Create your models here.
from django.conf import settings
from django.contrib.gis.db import models

# from django.utils import timezone


class Site(models.Model):
    """Model representing a site with geospatial boundaries."""

    name = models.CharField(
        max_length=255, unique=True, help_text="Unique name of the site"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_sites",
        help_text="Owner of the site",
    )
    boundary = models.PolygonField(
        srid=4326, help_text="Geospatial boundary of the site (WGS84)"
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="flexible json for additional site-specific data",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the site was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Timestamp when the site was last updated"
    )

    class Meta:
        """Meta options for the Site model."""

        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ["created_at"]

    def __str__(self: "Site") -> str:
        """Return String representation of the Site model."""
        return self.name


class GISLayer(models.Model):
    """Model representing a GIS layer associated with a site."""

    LAYER_TYPE_CHOICES = [
        ("CAD_PLAN", "CAD Plan"),
        ("GEOJSON_OVERLAY", "GeoJSON Overlay"),
        ("CONTOUR_LINES", "Contour Lines"),
        (
            "SATELLITE_IMAGE_FOOTPRINT",
            "Satellite Image Footprint",
        ),  # Future use for imagery boundaries
        ("OTHER", "Other"),
    ]
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="gis_layers",
        help_text="Site associated with this GIS layer",
    )
    name = models.CharField(max_length=255, help_text="Name of the GIS layer")
    file = models.FileField(upload_to="gis_layers/", help_text="GIS layer file data")
    layer_type = models.CharField(
        max_length=50,
        choices=LAYER_TYPE_CHOICES,
        default="OTHER",
        help_text="Type of GIS layer",
    )
    is_active = models.BooleanField(
        default=True, help_text="Indicates if the layer is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the GISLayer model."""

        verbose_name = "GIS Layer"
        verbose_name_plural = "GIS Layers"
        unique_together = ("site", "name")
        ordering = ["created_at"]

    def __str__(self: "GISLayer") -> str:
        """Return string representation of the GISLayer model."""
        return f"{self.name} ({self.name}) - {self.site.name}"


class SatelliteImage(models.Model):
    """Model representing a satellite image associated with a site."""

    IMAGE_SOURCE_CHOICES = [
        ("SENTINEL2", "Sentinel-2"),
        ("PLANETLABS", "Planet Labs"),
        ("MAXAR", "Maxar"),
        ("OTHER", "Other"),
    ]

    IMAGE_STATUS_CHOICES = [
        ("PENDING", "Pending Fetch"),
        ("FETCHED", "Image Fetched"),
        ("FAILED", "Fetch Failed"),
        ("PROCESSED", "Processed (Detections Complete)"),
        ("RAW_UPLOAD", "Raw Upload (Awaiting Processing)"),
    ]

    site = models.ForeignKey(
        "core.site",
        on_delete=models.CASCADE,
        related_name="satellite_images",
        help_text="Site associated with this satellite image",
    )
    image_file = models.FileField(
        upload_to="satellite_images/",
        help_text="Satellite image file data",
    )

    date_captured = models.DateTimeField(
        help_text="Date and time when the image was captured",
    )

    resolution_m_per_pixel = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Resolution of the image in meters per pixel",
    )

    source = models.CharField(
        max_length=50,
        choices=IMAGE_SOURCE_CHOICES,
        default="OTHER",
        help_text="Source of the satellite image",
    )

    cloud_cover_percentage = models.FloatField(
        null=True,
        blank=True,
        help_text="Percentage of cloud cover in the image",
    )

    footprint = models.PolygonField(
        srid=4326,
        help_text="Geospatial footprint of the satellite image (WGS84)",
    )

    metadata = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Flexible JSON for additional image-specific metadata",
    )

    status = models.CharField(
        max_length=50,
        choices=IMAGE_STATUS_CHOICES,
        default="PENDING",
        help_text="Current status of the satellite image",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the satellite image was created",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the satellite image was last updated",
    )

    class Meta:
        """Meta options for the SatelliteImage model."""

        verbose_name = "Satellite Image"
        verbose_name_plural = "Satellite Images"
        ordering = ["date_captured"]

    def __str__(self: "SatelliteImage") -> str:
        """Return string representation of the SatelliteImage model."""
        return f"{self.site.name} - {self.date_captured.strftime('%Y-%m-%d %H:%M:%S')}"
