"""view definitions for core app."""

from datetime import datetime

# Third-party imports
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django_filters import DateFromToRangeFilter, FilterSet
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

# Local application imports (your project's own modules)
from core.tasks import fetch_sentinel2_imagery

from .models import GISLayer, SatelliteImage, Site
from .serializers import GISLayerSerializer
from .serializers import SatelliteImageSerializer, SiteSerializer

from detection.tasks import process_image_detections


class IsSiteOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of a site or admins to access it."""

    def has_object_permission(
        self: "IsSiteOwnerOrAdmin", request: Request, view: APIView, obj: Site
    ) -> bool:
        """Allow access if the user is an admin or the owner of the site."""
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        if hasattr(obj, "owner") and obj.owner == request.user:
            return True
        if request.user and request.user.is_staff:
            return True
        return False


class SatelliteImageFilter(FilterSet):
    """FilterSet for SatelliteImage model."""

    date_captured = DateFromToRangeFilter(
        field_name="date_captured",
        label="Date Captured",
        help_text="Filter images by capture date range.",
    )
    site = filters.ModelChoiceFilter(
        queryset=Site.objects.all(),
        label="Site",
        help_text="Filter images by associated site.",
    )

    class Meta:
        """Meta options for SatelliteImageFilter."""

        model = SatelliteImage
        fields = {
            "site": ["exact"],
            "source": ["exact"],
            "status": ["exact"],
            "date_captured": ["exact", "range"],
        }


class SiteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Site instances."""

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated, IsSiteOwnerOrAdmin]

    def perform_create(self: "SiteViewSet", serializer: SiteSerializer) -> None:
        """Set the owner of the site to the requesting user upon creation."""
        serializer.save(owner=self.request.user)

    @action(
        detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def gis_layers(self: "SiteViewSet", request: Request, pk: int = None) -> Response:
        """Retrieve GIS layers associated with a specific site."""
        site = get_object_or_404(Site, pk=pk)
        gis_layers = site.gis_layers.all()
        serializer = GISLayerSerializer(
            gis_layers, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path="fetch-imagery",
        permission_classes=[permissions.IsAuthenticated, IsSiteOwnerOrAdmin],
    )
    def fetch_imagery(
        self: "SiteViewSet", request: Request, pk: int = None
    ) -> Response:
        """Fetch Sentinel-2 imagery for the site within a specified date range."""
        site = get_object_or_404(Site, pk=pk)
        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")

        if not start_date_str or not end_date_str:
            return Response(
                {"error": "Both start_date and end_date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            datetime.fromisoformat(start_date_str)
            datetime.fromisoformat(end_date_str)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fetch_sentinel2_imagery.delay(site.id, start_date_str, end_date_str)

        return Response(
            {"message": "Imagery fetch initiated successfully."},
            status=status.HTTP_202_ACCEPTED,
        )


class GISLayerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing GISLayer instances."""

    queryset = GISLayer.objects.all()
    serializer_class = GISLayerSerializer
    permission_classes = [permissions.IsAuthenticated, IsSiteOwnerOrAdmin]

    def perform_create(self: "GISLayerViewSet", serializer: GISLayerSerializer) -> None:
        """Set the owner of the GIS layer to the requesting user upon creation."""
        serializer.save(owner=self.request.user)

    def get_queryset(self: "GISLayerViewSet") -> QuerySet:
        """Filter GIS layers by the requesting user's sites or site_pk in URL."""
        queryset = super().get_queryset()
        site_pk = self.kwargs.get("site_pk")
        if site_pk:
            queryset = queryset.filter(site__id=site_pk)
        if self.request.user.is_authenticated:
            queryset = queryset.filter(site__owner=self.request.user)
        return queryset


class SatelliteImageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet to list and retrieve SatelliteImage instances for a specific site."""

    serializer_class = SatelliteImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SatelliteImageFilter

    def get_queryset(self: "SatelliteImageViewSet") -> QuerySet:
        """Return SatelliteImages filtered by site_pk in the URL."""
        site_pk = self.kwargs.get("site_pk")
        if site_pk is None:
            return SatelliteImage.objects.none()
        return SatelliteImage.objects.filter(site__pk=site_pk).select_related("site")

    @action(
        detail=True,
        methods=["get"],
        url_path="run-detection",
        permission_classes=[permissions.IsAuthenticated],
    )
    def run_detection(
        self: "SatelliteImageViewSet", request: Request, **kwargs: any
    ) -> Response:
        """Trigger AI detection processing for a specific SatelliteImage."""
        # Access URL parameters from self.kwargs
        site_pk = self.kwargs.get("site_pk")
        pk = self.kwargs.get("pk")  # This is the SatelliteImage ID

        # Check if site_pk and pk are available (should be from URL)
        if not site_pk or not pk:
            return Response(
                {
                    "error": "Both site_pk and image ID (pk) must be provided in the URL."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        satellite_image = get_object_or_404(
            SatelliteImage, pk=pk, site__pk=self.kwargs.get("site_pk")
        )

        if not request.user.is_staff and satellite_image.site.owner != request.user:
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        process_image_detections.delay(satellite_image.pk)

        return Response(
            {"message": "AI detection processing initiated successfully."},
            status=status.HTTP_202_ACCEPTED,
        )
