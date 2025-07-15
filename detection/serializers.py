"""Serializers for the detection app."""

import json  # Required for json.loads in get_geojson_location
from rest_framework import serializers

from .models import Detection, ChangeLog  # Import both models


class DetectionSerializer(serializers.ModelSerializer):
    """Serializer for the Detection model.

    Outputs 'location' as a GeoJSON Point Feature via 'geojson_location' field.
    """

    satellite_image_id = serializers.ReadOnlyField(source="satellite_image.id")
    site_name = serializers.ReadOnlyField(source="satellite_image.site.name")

    # SerializerMethodField to output location as GeoJSON
    geojson_location = serializers.SerializerMethodField()
    coordinates = serializers.JSONField()

    class Meta:
        """Meta class for DetectionSerializer."""

        model = Detection
        # Explicitly list all fields, including the new geojson_location
        fields = (
            "id",
            "satellite_image",
            "satellite_image_id",
            "site_name",
            "detected_class",
            "coordinates",
            "confidence",
            "location",  # Keep raw location field
            "geojson_location",  # The GeoJSON representation for frontend mapping
            "timestamp",
            "metadata",
        )
        read_only_fields = ("timestamp",)  # Automatically set by auto_now_add

    def get_geojson_location(
        self: "DetectionSerializer", obj: Detection
    ) -> dict | None:
        """Return the location PointField as a GeoJSON dictionary."""
        if obj.location:
            # Assuming obj.location is a GEOSGeometry object that has a .geojson property
            # which returns a JSON string.
            return json.loads(obj.location.geojson)
        return None


class ChangeLogSerializer(serializers.ModelSerializer):
    """Serializer for the ChangeLog model.

    Provides formatted dates for related images.
    """

    site_name = serializers.ReadOnlyField(source="site.name")
    # Use DateTimeField for formatted output of related image capture dates
    image_before_date = serializers.DateTimeField(
        source="image_before.date_captured", read_only=True, format="%Y-%m-%d %H:%M:%S"
    )
    image_after_date = serializers.DateTimeField(
        source="image_after.date_captured", read_only=True, format="%Y-%m-%d %H:%M:%S"
    )

    class Meta:
        """Meta class for ChangeLogSerializer."""

        model = ChangeLog
        fields = (
            "id",
            "site",
            "site_name",
            "image_before",
            "image_before_date",
            "image_after",
            "image_after_date",
            "change_type",
            "description",
            "metadata",
            "timestamp",
        )
        read_only_fields = ("timestamp",)  # Automatically set by auto_now_add
