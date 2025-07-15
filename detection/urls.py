"""urls for detection app."""

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import DetectionViewSet, ChangeLogViewSet  # Import your ViewSets

# Router for top-level viewsets (e.g., /api/detections/, /api/change-logs/)
router = DefaultRouter()
router.register(r"detections", DetectionViewSet, basename="detection")
router.register(r"change-logs", ChangeLogViewSet, basename="change-log")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "sites/<int:site_pk>/detections/",
        DetectionViewSet.as_view({"get": "list"}),
        name="site-detection-list",
    ),
    path(
        "sites/<int:site_pk>/detections/<int:pk>/",
        DetectionViewSet.as_view({"get": "retrieve"}),
        name="site-detection-detail",
    ),
    path(
        "sites/<int:site_pk>/changes/",
        ChangeLogViewSet.as_view({"get": "list"}),
        name="site-change-log-list",
    ),
    path(
        "sites/<int:site_pk>/changes/<int:pk>/",
        ChangeLogViewSet.as_view({"get": "retrieve"}),
        name="site-change-log-detail",
    ),
]
