"""Views for the alerts application."""

from django.db.models import QuerySet, Model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters import DateFromToRangeFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend

from .models import Alert, AlertRule
from .serializers import AlertRuleSerializer, AlertSerializer


class IsSiteOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it.

    Allows admin users full access.
    """

    def has_object_permission(
        self: "IsSiteOwnerOrAdmin", request: Request, view: APIView, obj: Model
    ) -> bool:
        """Allow access if the user is an admin or the owner of the associated site."""
        # Allow read access to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Check if the object has a 'site' attribute (like AlertRule)
        if hasattr(obj, "site") and obj.site.owner == request.user:
            return True
        # For Detections (if this permission were used directly there), check via satellite_image.site.owner
        if (
            hasattr(obj, "satellite_image")
            and hasattr(obj.satellite_image, "site")
            and obj.satellite_image.site.owner == request.user
        ):
            return True
        # For ChangeLog (if used directly there), check via site.owner
        # For Alert specifically, it can be linked via change_log.site.owner
        if (
            hasattr(obj, "change_log")
            and obj.change_log
            and obj.change_log.site
            and obj.change_log.site.owner == request.user
        ):
            return True

        # Allow staff (admin) users full access
        if request.user and request.user.is_staff:
            return True
        return False


class AlertFilter(FilterSet):
    """FilterSet for the Alert model."""

    triggered_on = DateFromToRangeFilter(field_name="triggered_on")

    class Meta:
        """Meta options for AlertFilter."""

        model = Alert
        fields = {
            "site": ["exact"],
            "type": ["exact"],
            "status": ["exact"],
            "user": ["exact"],  # Filter by specific user
            "triggered_on": ["exact", "range"],
        }


class AlertRuleFilter(FilterSet):
    """FilterSet for the AlertRule model."""

    class Meta:
        """Meta options for AlertRuleFilter."""

        model = AlertRule
        fields = {
            "site": ["exact"],
            "rule_type": ["exact"],
            "is_active": ["exact"],
            "target_class": ["exact"],
        }


class AlertViewSet(
    viewsets.ModelViewSet
):  # ModelViewSet for full CRUD on alerts (though system-generated)
    """API endpoint that allows Alerts to be viewed, updated, or deleted."""

    # Optimize query: pre-fetch related site, user, and change_log
    queryset = Alert.objects.all().select_related(
        "site", "user", "change_log__site"
    )  # Add change_log__site for related data

    serializer_class = AlertSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsSiteOwnerOrAdmin,
    ]  # Apply permission

    filter_backends = [DjangoFilterBackend]
    filterset_class = AlertFilter

    def get_queryset(self: "AlertViewSet") -> QuerySet[Alert]:
        """Filter alerts to only show for sites user owns or if they are staff."""
        queryset = super().get_queryset()
        # Filter alerts to only show for sites user owns or if they are staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(site__owner=self.request.user)
        return queryset

    @action(detail=True, methods=["patch"], url_path="mark-as-read")
    def mark_as_read(
        self: "AlertViewSet", request: Request, pk: int = None
    ) -> Response:
        """Mark an Alert as 'READ'."""
        alert = get_object_or_404(Alert, pk=pk)
        self.check_object_permissions(request, alert)  # Uses IsSiteOwnerOrAdmin

        if alert.status == "UNREAD":
            alert.status = "READ"
            alert.save(update_fields=["status"])
            return Response(
                {"status": "alert marked as read"}, status=status.HTTP_200_OK
            )
        return Response(
            {"status": f"alert is already {alert.status}"}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["patch"], url_path="mark-as-resolved")
    def mark_as_resolved(
        self: "AlertViewSet", request: Request, pk: int = None
    ) -> Response:
        """Mark an Alert as 'RESOLVED'.

        URL: /api/alerts/{id}/mark-as-resolved/
        """
        alert = get_object_or_404(Alert, pk=pk)
        self.check_object_permissions(request, alert)  # Uses IsSiteOwnerOrAdmin

        if alert.status != "RESOLVED":
            alert.status = "RESOLVED"
            alert.save(update_fields=["status"])
            return Response(
                {"status": "alert marked as resolved"}, status=status.HTTP_200_OK
            )
        return Response(
            {"status": f"alert is already {alert.status}"}, status=status.HTTP_200_OK
        )


class AlertRuleViewSet(viewsets.ModelViewSet):  # ModelViewSet for full CRUD on rules
    """API endpoint that allows AlertRules to be viewed or edited."""

    queryset = AlertRule.objects.all().select_related("site")
    serializer_class = AlertRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsSiteOwnerOrAdmin]

    filter_backends = [DjangoFilterBackend]
    filterset_class = AlertRuleFilter

    def get_queryset(self: "AlertRuleViewSet") -> QuerySet[AlertRule]:
        """Filter rules to only show for sites user owns or if they are staff."""
        queryset = super().get_queryset()
        # Filter rules to only show for sites user owns or if they are staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(site__owner=self.request.user)
        return queryset

    def perform_create(
        self: "AlertRuleViewSet", serializer: AlertRuleSerializer
    ) -> None:
        """Create a new AlertRule instance.

        Ensure site object is valid and its owner is the requesting user (or admin).
        """
        site = serializer.validated_data["site"]
        if not self.request.user.is_staff and site.owner != self.request.user:
            raise permissions.PermissionDenied(
                "You can only create rules for sites you own or if you are an admin."
            )
        serializer.save()
