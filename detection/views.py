"""Views for the detection app."""
from django.db.models import QuerySet, Model  # Import Model for type hinting obj
from rest_framework import permissions, viewsets
from rest_framework.request import Request
from rest_framework.views import APIView

# from rest_framework.response import Response # Removed: F401 unused import
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, DateFromToRangeFilter

from .models import (
    Detection,
    ChangeLog,
)  # Ensure Site is imported for type hinting in IsSiteOwnerOrAdmin
from .serializers import (
    DetectionSerializer,
    ChangeLogSerializer,
)


# IMPORTANT: Copy the IsSiteOwnerOrAdmin permission from core/views.py for now
# We will unify this permission into a shared 'auth' app in Sprint 5.
class IsSiteOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of an object (Site, GISLayer, Detection, ChangeLog) to edit it.

    Allows admin users to edit objects. This is a basic version.
    """

    def has_object_permission(
        self: "IsSiteOwnerOrAdmin", request: Request, view: APIView, obj: Model
    ) -> bool:
        """Allow access if the user is an admin or the owner of the associated site."""
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Check if the object has an 'owner' attribute (like Site)
        if hasattr(obj, "owner") and obj.owner == request.user:
            return True
        # For Detections, they are owned indirectly via SatelliteImage.site.owner.
        if (
            hasattr(obj, "satellite_image")
            and hasattr(obj.satellite_image, "site")
            and obj.satellite_image.site.owner == request.user
        ):
            return True
        # For ChangeLogs, they are owned indirectly via ChangeLog.site.owner.
        if hasattr(obj, "site") and obj.site.owner == request.user:
            return True

        # is_staff implies admin
        if request.user and request.user.is_staff:
            return True
        return False


# --- Filters for API ---


class DetectionFilter(FilterSet):
    """FilterSet for the Detection model."""

    class Meta:
        """Meta class for DetectionFilter."""

        model = Detection
        fields = {
            "satellite_image": ["exact"],
            "detected_class": ["exact"],
            "confidence": ["gte", "lte", "exact"],  # Example range filters
            "timestamp": ["gte", "lte", "range"],  # For date range filtering
        }


class ChangeLogFilter(FilterSet):
    """FilterSet for the ChangeLog model."""

    timestamp = DateFromToRangeFilter(
        field_name="timestamp"
    )  # Provides `timestamp_after`, `timestamp_before`

    class Meta:
        """Meta class for ChangeLogFilter."""

        model = ChangeLog
        fields = {
            "site": ["exact"],
            "change_type": ["exact"],
            "timestamp": [
                "exact",
                "range",
            ],  # `range` maps to the DateFromToRangeFilter
        }


# --- ViewSets ---


class DetectionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows Detections to be viewed.

    Supports filtering.
    """

    # Optimize query: pre-fetch related SatelliteImage and its Site owner
    queryset = Detection.objects.all().select_related("satellite_image__site")
    serializer_class = DetectionSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsSiteOwnerOrAdmin,
    ]  # Apply permission

    filter_backends = [DjangoFilterBackend]
    filterset_class = DetectionFilter

    def get_queryset(self: "DetectionViewSet") -> "QuerySet[Detection]":
        """Override to filter Detections by the requesting user's sites."""
        queryset = super().get_queryset()
        # Optional: Filter by site_pk if nested under /sites/<pk>/detections/
        site_pk = self.kwargs.get("site_pk")
        if site_pk:
            queryset = queryset.filter(satellite_image__site__pk=site_pk)
        return queryset


class ChangeLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows ChangeLogs to be viewed.

    Supports filtering by site and date range.
    """

    # Optimize query: pre-fetch related Site, and before/after images
    queryset = ChangeLog.objects.all().select_related(
        "site", "image_before", "image_after"
    )
    serializer_class = ChangeLogSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsSiteOwnerOrAdmin,
    ]  # Apply permission

    filter_backends = [DjangoFilterBackend]
    filterset_class = ChangeLogFilter

    def get_queryset(self: "ChangeLogViewSet") -> "QuerySet[ChangeLog]":
        """Override to filter ChangeLogs by the requesting user's sites."""
        queryset = super().get_queryset()
        # Optional: Filter by site_pk if nested under /sites/<pk>/changes/
        site_pk = self.kwargs.get("site_pk")
        if site_pk:
            queryset = queryset.filter(site__pk=site_pk)
        return queryset
