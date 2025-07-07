"""models module for core app."""

# Create your models here.
from django.conf import settings
from django.db import models

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
    is_active = models.BooleanField(
        default=True, help_text="Indicates if the site is currently active"
    )

    class Meta:
        """Meta options for the Site model."""

        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ["created_at"]

    def __str__(self: "Site") -> str:
        """Return String representation of the Site model."""
        return self.name
