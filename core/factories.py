"""factories.py."""

# import os

# import factory
# from django.contrib.auth import get_user_model
# from django.contrib.gis.geos import GEOSGeometry, Polygon
# from django.core.files.uploadedfile import SimpleUploadedFile
# from factory.django import DjangoModelFactory

# from core.models import GISLayer, Site

# User = get_user_model()


# class UserFactory(DjangoModelFactory):
#     """Factory for creating User instances."""

#     class Meta:
#         model = User
#         django_get_or_create = ("username",)

#     username = factory.Sequence(lambda n: f"user{n}")
#     email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
#     password = factory.PostGenerationMethodCall("set_password", "password123")
#     is_staff = False
#     is_active = True
#     is_superuser = False


# class SiteFactory(DjangoModelFactory):
#     """Factory for creating Site instances."""

#     class Meta:
#         model = Site

#         name = factory.Sequence(lambda n: f"Site {n}")
#         owner = factory.SubFactory(UserFactory)
#         boundary = factory.LazyFunction(
#             lambda: GEOSGeometry("POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))", srid=4326)
#         )
#         metadata = {}
#         # created_at = factory.Faker('date_time_this_year')
#         # updated_at = factory.Faker('date_time_this_year')


# class GISLayerFactory(DjangoModelFactory):
#     """Factory for creating GISLayer instances."""

#     class Meta:
#         model = GISLayer

#     name = factory.Sequence(lambda n: f"Layer {n}")
#     site = factory.SubFactory(SiteFactory)
#     layer_type = factory.Iterator(GISLayer.LAYER_TYPE_CHOICES, getter=lambda c: c[0])
#     file = factory.LazyFunction(
#         lambda: SimpleUploadedFile(
#             name="test_file.geojson",
#             content=b'{"type": "FeatureCollection", "features": []}',
#             content_type="application/geo+json",
#         )
#     )
