"""core/urls.py."""

from django.urls import path

urlpatterns = [
    path("example/", lambda request: None, name="example"),  # Example endpoint
]
