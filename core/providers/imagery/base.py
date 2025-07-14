"""Base class for satellite imagery providers."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.contrib.gis.geos import GEOSGeometry


class BaseImageryProvider(ABC):
    """Abstract base class for satellite imagery providers."""

    def __init__(
        self: "BaseImageryProvider",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        """Initialize the provider with optional API key and base URL."""
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def query_imagery(
        self: "BaseImageryProvider",
        bbox: GEOSGeometry,
        start_date: datetime,
        end_date: datetime,
        cloud_cover_max: float = 100.0,
        resolution_max: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query the imagery provider for images within the specified criteria.

        Args:
            bbox: A GEOSGeometry object (Polygon) representing the area of interest.
            start_date: Start datetime for image capture.
            end_date: End datetime for image capture.
            cloud_cover_max: Maximum allowed cloud cover percentage (0–100).
            resolution_max: Maximum desired resolution in meters per pixel.

        Returns:
            A list of dictionaries, each containing raw metadata of available images.
        """
        pass

    @abstractmethod
    def get_image_details(self: "BaseImageryProvider", image_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed metadata for a specific image by its ID.

        Args:
            image_id: Unique identifier of the image.

        Returns:
            A dictionary containing metadata details of the image.
        """
        pass

    @abstractmethod
    def get_image_file_data(self: "BaseImageryProvider", image_url: str) -> bytes:
        """
        Retrieve raw byte data of an image from the given URL.

        Args:
            image_url: URL to download the image.

        Returns:
            A byte array representing the image file content.
        """
        pass

    @abstractmethod
    def parse_api_metadata(
        self: "BaseImageryProvider", raw_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse raw API metadata into a standardized format.

        Args:
            raw_metadata: Raw metadata returned from the imagery provider.

        Returns:
            A dictionary formatted to match SatelliteImage model fields,
            including keys like 'date_captured', 'resolution_m_per_pixel', 'source',
            'cloud_cover_percentage', 'footprint', and 'metadata'.
        """
        pass
