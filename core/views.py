"""view definitions for core app."""

from datetime import datetime  # Line 6

# Third-party imports
from django.db.models import QuerySet  # Line 9
from django.shortcuts import get_object_or_404  # Line 10
from django_filters import DateFromToRangeFilter, FilterSet  # Line 11
from django_filters import rest_framework as filters  # Line 12
from django_filters.rest_framework import DjangoFilterBackend  # Line 13
from rest_framework import permissions, status, viewsets  # Line 14
from rest_framework.decorators import action  # Line 15
from rest_framework.request import Request  # Line 16
from rest_framework.response import Response  # Line 17
from rest_framework.views import APIView  # Line 18

# Local application imports (your project's own modules)
from core.tasks import fetch_sentinel2_imagery  # Line 21

from .models import GISLayer, SatelliteImage, Site  # Line 25
from .serializers import GISLayerSerializer  # Line 26
from .serializers import SatelliteImageSerializer, SiteSerializer  # Line 27


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
