"""admin module for core app."""

from django.contrib.gis import admin

from .models import GISLayer, Site


# Register your models here.
@admin.register(Site)
class SiteAdmin(admin.GISModelAdmin):
    """Admin interface for the Site model."""

    list_display = ("name", "owner", "created_at", "updated_at")
    list_filter = ("owner", "created_at", "updated_at")
    default_lat = 0
    default_lon = 0
    default_zoom = 3


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
