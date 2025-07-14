"""Serializers module for the core app."""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import GISLayer, SatelliteImage, Site


class SiteSerializer(GeoFeatureModelSerializer):
    """Serializer for the Site model."""

    owner_username = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        """Meta options for the SiteSerializer."""

        model = Site
        geo_field = "boundary"
        fields = (
            "id",
            "name",
            "owner",
            "owner_username",
            "boundary",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def create(self: "SiteSerializer", validated_data: dict) -> Site:
        """Create a new Site instance."""
        return super().create(validated_data)

    def update(self: "SiteSerializer", instance: Site, validated_data: dict) -> Site:
        """Update an existing Site instance."""
        return super().update(instance, validated_data)


class GISLayerSerializer(serializers.ModelSerializer):
    """Serializer for the GISLayer model."""

    class Meta:
        """Meta options for the GISLayerSerializer."""

        model = GISLayer
        fields = (
            "id",
            "site",
            "name",
            "file",
            "layer_type",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class SatelliteImageSerializer(GeoFeatureModelSerializer):
    """Serializer for the SatelliteImage model with GeoJSON footprint."""

    site_name = serializers.ReadOnlyField(source="site.name")

    class Meta:
        """Meta options for the SatelliteImageSerializer."""

        model = SatelliteImage
        geo_field = "footprint"
        fields = (
            "id",
            "site",
            "site_name",
            "image_file",
            "date_captured",
            "resolution_m_per_pixel",
            "source",
            "cloud_cover_percentage",
            "footprint",
            "metadata",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
