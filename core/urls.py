"""core/urls.py."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GISLayerViewSet, SiteViewSet

router = DefaultRouter()
router.register(r"sites", SiteViewSet, basename="site")
router.register(r"gis-layers", GISLayerViewSet, basename="gis-layer")


urlpatterns = [
    path("", include(router.urls)),  # Include the router's URLs
    path("example/", lambda request: None, name="example"),  # Example endpoint
]
