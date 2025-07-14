"""core/urls.py."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GISLayerViewSet, SatelliteImageViewSet, SiteViewSet

router = DefaultRouter()
router.register(r"sites", SiteViewSet, basename="site")
router.register(r"gis-layers", GISLayerViewSet, basename="gis-layer")


urlpatterns = [
    path("", include(router.urls)),  # Include the router's URLs
    path("example/", lambda request: None, name="example"),  # Example endpoint
    path(
        "sites/<int:site_pk>/images/",
        SatelliteImageViewSet.as_view({"get": "list"}),
        name="site-satelliteimage-list",
    ),
    path(
        "sites/<int:site_pk>/images/<int:image_pk>/",
        SatelliteImageViewSet.as_view({"get": "retrieve"}),
        name="site-satelliteimage-detail",
    ),
]
