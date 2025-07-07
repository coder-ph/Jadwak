"""views."""
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request  # Import Request
from rest_framework.response import Response
from rest_framework.views import APIView  # Import APIView

from .models import GISLayer, Site
from .serializers import GISLayerSerializer, SiteSerializer


# Create your views here.
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

    # ---viewsets---


class SiteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Site instances."""

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated, IsSiteOwnerOrAdmin]

    def perform_create(self: "SiteViewSet", serializer: "SiteSerializer") -> None:
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


class GISLayerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing GISLayer instances."""

    queryset = GISLayer.objects.all()
    serializer_class = GISLayerSerializer
    permission_classes = [permissions.IsAuthenticated, IsSiteOwnerOrAdmin]

    def perform_create(
        self: "GISLayerViewSet", serializer: "GISLayerSerializer"
    ) -> None:
        """Set the owner of the GIS layer to the requesting user upon creation."""
        serializer.save(owner=self.request.user)

    def get_queryset(self: "GISLayerViewSet") -> "QuerySet[GISLayer]":
        """Override to filter GIS layers by the requesting user's sites."""
        queryset = super().get_queryset()
        site_pk = self.kwargs.get("site_pk")
        if site_pk:
            queryset = queryset.filter(site__id=site_pk)
        if self.request.user.is_authenticated:
            queryset = queryset.filter(site__owner=self.request.user)

        return queryset
