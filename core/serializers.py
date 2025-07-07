"""serializers module for core app."""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import GISLayer, Site


class SiteSerializer(GeoFeatureModelSerializer):
    """Serializer for the Site model."""

    owner_username = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        """meta options for the SiteSerializer."""

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
            "name",
            "site",
            "layer_type",
            "data",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
