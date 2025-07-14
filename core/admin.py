"""admin module for core app."""

from django.contrib.gis import admin

from .models import GISLayer, SatelliteImage, Site


# Register your models here.
@admin.register(Site)
class SiteAdmin(admin.GISModelAdmin):
    """Admin interface for the Site model."""

    list_display = ("name", "owner", "created_at", "updated_at")
    list_filter = ("owner", "created_at", "updated_at")
    default_lat = 36.817223
    default_lon = -1.2863
    default_zoom = 12


@admin.register(GISLayer)
class GISLayerAdmin(admin.ModelAdmin):
    """Admin interface for the GISLayer model."""

    list_display = ("name", "site", "layer_type", "created_at", "is_active")
    list_filter = ("site", "layer_type", "created_at", "is_active")
    search_fields = ("site__name", "name")
    raw_id_fields = ("site",)

    # def get_queryset(self, request):
    #     """Override to select related Site for performance."""
    #     return super().get_queryset(request).select_related("site")


@admin.register(SatelliteImage)
class SatelliteImageAdmin(admin.GISModelAdmin):
    """Admin interface for the SatelliteImage model."""

    list_display = (
        "site",
        "date_captured",
        "source",
        "resolution_m_per_pixel",
        "cloud_cover_percentage",
        "status",
        "created_at",
    )
    list_filter = ("site", "source", "status", "date_captured")
    search_fields = (
        "site__name",
        "source",
        "metadata__id",
    )  # You can search by site name, source, or metadata
    raw_id_fields = ("site",)
    default_lon = 36.817223
    default_lat = -1.286389
    default_zoom = 8
