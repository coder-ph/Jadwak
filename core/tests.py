"""tests module for core app."""

# import json

# import pytest
# from django.contrib.gis.geos import GEOSGeometry, Polygon
# from django.core.files.uploadedfile import SimpleUploadedFile
# from django.test import TestCase
# from django.urls import reverse
# from factories import GISLayerFactory, SiteFactory, UserFactory
# from rest_framework.test import APIClient

# from core.models import GISLayer, Site

# # Create your tests here.


# @pytest.fixture
# def api_client():
#     """Fixture to provide an API client for tests."""
#     return APIClient()


# @pytest.fixture
# def authenticated_client(api_client):
#     """Fixture to provide an authenticated API client."""
#     user = UserFactory()
#     api_client.force_authenticate(user=user)
#     return api_client


# @pytest.fixture
# def admin_client(api_client):
#     """Fixture to provide an admin API client."""
#     admin_user = UserFactory(is_staff=True, is_superuser=True)
#     api_client.force_authenticate(user=admin_user)
#     return api_client


# @pytest.fixture
# def regular_user(api_client):
#     """Fixture to provide a regular user."""
#     return UserFactory


# @pytest.fixture
# def admin_user(api_client):
#     """Fixture to provide an admin user."""
#     return UserFactory(is_staff=True, is_superuser=True)


# @pytest.mark.django_db
# def test_site_model_creation():
#     """Test that a site can be created with a valid data."""
#     owner = UserFactory()
#     polygon = Polygon(((0, 0), (1, 0), (1, 1), (0, 1), (0, 0)), srid=4326)
#     site = Site.objects.create(
#         name="Test Site",
#         owner=owner,
#         boundary=polygon,
#         metadata={"description": "A test site"},
#     )

#     assert site.pk
#     assert site.name == "Test Site"
#     assert site.owner == owner
#     assert site.boundary.equals(polygon)
#     assert site.metadata["description"] == "A test site"
#     assert site.created_at is not None
#     assert site.updated_at is not None


# @pytest.mark.django_db
# def test_gislayer_model_creation():
#     """Test that a GISLayer can be created with valid data."""
#     site = SiteFactory()
#     dummy_file = SimpleUploadedFile(
#         "test_layer.geojson", b"{}", content_type="application/geo+json"
#     )
#     gis_layer = GISLayer.objects.create(
#         site=site, name="Test Layer 1", file=dummy_file, layer_type="GEOJSON_OVERLAY"
#     )

#     assert gis_layer.pk is not None
#     assert gis_layer.name == "Test Layer 1"
#     assert gis_layer.site == site
#     assert gis_layer.file.name.endswith(
#         "test_layer.geojson"
#     )  # Check if file name is correct
#     assert gis_layer.layer_type == "GEOJSON_OVERLAY"
#     assert gis_layer.is_active is True


# # --- API Tests for Site Model ---


# @pytest.mark.django_db
# def test_site_list_unauthenticated(api_client):
#     """Test that unauthenticated users cannot list sites."""
#     SiteFactory.create_batch(3)  # Create some dummy sites
#     url = reverse("site-list")
#     response = api_client.get(url)
#     assert response.status_code == 401  # Unauthorized


# @pytest.mark.django_db
# def test_site_list_authenticated(authenticated_client):
#     """Test that authenticated users can list sites."""
#     # Create sites owned by different users
#     my_site = SiteFactory(owner=authenticated_client.user)
#     other_site = SiteFactory()
#     url = reverse("site-list")
#     response = authenticated_client.get(url)
#     assert response.status_code == 200
#     assert (
#         len(response.data["results"]) == 2
#     )  # Should see all sites (read permission is allowAny for now)
#     assert (
#         response.data["results"][0]["name"] == my_site.name
#         or response.data["results"][1]["name"] == my_site.name
#     )


# @pytest.mark.django_db
# def test_site_create_authenticated(authenticated_client):
#     """Test that authenticated users can create a site."""
#     url = reverse("site-list")
#     data = {
#         "name": "New Test Site",
#         "boundary": {
#             "type": "Polygon",
#             "coordinates": [
#                 [[0.1, 0.1], [0.1, 0.2], [0.2, 0.2], [0.2, 0.1], [0.1, 0.1]]
#             ],
#         },
#         "metadata": {"project_id": "XYZ123"},
#     }
#     response = authenticated_client.post(url, data, format="json")
#     assert response.status_code == 201  # Created
#     assert Site.objects.count() == 1
#     created_site = Site.objects.first()
#     assert created_site.name == "New Test Site"
#     assert (
#         created_site.owner == authenticated_client.user
#     )  # Owner should be set automatically


# @pytest.mark.django_db
# def test_site_retrieve_authenticated(authenticated_client):
#     """Test that authenticated users can retrieve site details."""
#     site = SiteFactory(owner=authenticated_client.user)
#     url = reverse("site-detail", args=[site.pk])
#     response = authenticated_client.get(url)
#     assert response.status_code == 200
#     assert response.data["name"] == site.name
#     assert response.data["owner_username"] == site.owner.username


# @pytest.mark.django_db
# def test_site_update_owner(authenticated_client):
#     """Test that site owner can update their own site."""
#     site = SiteFactory(owner=authenticated_client.user)
#     url = reverse("site-detail", args=[site.pk])
#     data = {"name": "Updated Site Name"}
#     response = authenticated_client.patch(url, data, format="json")
#     assert response.status_code == 200
#     site.refresh_from_db()
#     assert site.name == "Updated Site Name"


# @pytest.mark.django_db
# def test_site_update_non_owner_forbidden(authenticated_client):
#     """Test that a non-owner cannot update another user's site."""
#     other_user = UserFactory()
#     site = SiteFactory(owner=other_user)
#     url = reverse("site-detail", args=[site.pk])
#     data = {"name": "Attempted Update"}
#     response = authenticated_client.patch(url, data, format="json")
#     assert response.status_code == 403  # Forbidden


# @pytest.mark.django_db
# def test_site_delete_owner(authenticated_client):
#     """Test that site owner can delete their own site."""
#     site = SiteFactory(owner=authenticated_client.user)
#     url = reverse("site-detail", args=[site.pk])
#     response = authenticated_client.delete(url)
#     assert response.status_code == 204  # No Content
#     assert Site.objects.count() == 0


# @pytest.mark.django_db
# def test_site_delete_non_owner_forbidden(authenticated_client):
#     """Test that a non-owner cannot delete another user's site."""
#     other_user = UserFactory()
#     site = SiteFactory(owner=other_user)
#     url = reverse("site-detail", args=[site.pk])
#     response = authenticated_client.delete(url)
#     assert response.status_code == 403  # Forbidden
#     assert Site.objects.count() == 1  # Site should still exist


# # --- API Tests for GISLayer Model ---


# @pytest.mark.django_db
# def test_gislayer_create_authenticated(authenticated_client):
#     """Test that authenticated users can create a GISLayer."""
#     site = SiteFactory(
#         owner=authenticated_client.user
#     )  # Create a site owned by the authenticated user
#     url = reverse("gis-layer-list")
#     dummy_file_content = b'{"name": "test_layer_content"}'
#     dummy_file = SimpleUploadedFile(
#         "upload.json", dummy_file_content, content_type="application/json"
#     )

#     data = {
#         "site": site.pk,  # Link to the site by its primary key
#         "name": "New GIS Layer",
#         "file": dummy_file,
#         "layer_type": "GEOJSON_OVERLAY",
#     }
#     response = authenticated_client.post(
#         url, data, format="multipart"
#     )  # Use multipart for file uploads
#     assert response.status_code == 201
#     assert GISLayer.objects.count() == 1
#     created_layer = GISLayer.objects.first()
#     assert created_layer.name == "New GIS Layer"
#     assert created_layer.site == site
#     assert created_layer.file.read() == dummy_file_content  # Verify content


# @pytest.mark.django_db
# def test_gislayer_retrieve_authenticated(authenticated_client):
#     """Test that authenticated users can retrieve GISLayer details."""
#     site = SiteFactory(owner=authenticated_client.user)
#     gis_layer = GISLayerFactory(site=site)
#     url = reverse("gis-layer-detail", args=[gis_layer.pk])
#     response = authenticated_client.get(url)
#     assert response.status_code == 200
#     assert response.data["name"] == gis_layer.name


# @pytest.mark.django_db
# def test_gislayer_delete_owner(authenticated_client):
#     """Test that site owner can delete their GISLayer."""
#     site = SiteFactory(owner=authenticated_client.user)
#     gis_layer = GISLayerFactory(site=site)
#     url = reverse("gis-layer-detail", args=[gis_layer.pk])
#     response = authenticated_client.delete(url)
#     assert response.status_code == 204
#     assert GISLayer.objects.count() == 0


# @pytest.mark.django_db
# def test_gislayer_delete_non_owner_forbidden(authenticated_client):
#     """Test that a non-owner cannot delete another user's GISLayer."""
#     other_user = UserFactory()
#     site = SiteFactory(owner=other_user)
#     gis_layer = GISLayerFactory(site=site)
#     url = reverse("gis-layer-detail", args=[gis_layer.pk])
#     response = authenticated_client.delete(url)
#     assert response.status_code == 403
#     assert GISLayer.objects.count() == 1


# # --- Test Custom Action: /api/sites/{id}/gis_layers/ ---


# @pytest.mark.django_db
# def test_site_gis_layers_action(authenticated_client):
#     """Test the custom action to list GIS layers for a site."""
#     site = SiteFactory(owner=authenticated_client.user)
#     layer1 = GISLayerFactory(site=site, name="Layer Alpha")
#     layer2 = GISLayerFactory(site=site, name="Layer Beta")
#     # Layer for another site
#     SiteFactory()
#     GISLayerFactory()

#     url = reverse(
#         "site-gis-layers", args=[site.pk]
#     )  # 'site-gis-layers' is the name generated by DRF for custom action
#     response = authenticated_client.get(url)
#     assert response.status_code == 200
#     assert len(response.data) == 2  # Should only return layers for this specific site
#     assert (
#         response.data[0]["name"] == layer1.name
#         or response.data[1]["name"] == layer1.name
#     )
#     assert (
#         response.data[0]["name"] == layer2.name
#         or response.data[1]["name"] == layer2.name
#     )
