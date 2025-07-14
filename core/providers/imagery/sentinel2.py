"""Mock implementation of a Sentinel-2 satellite imagery provider for testing."""

import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.utils import timezone as django_timezone

from .base import BaseImageryProvider


class Sentinel2Provider(BaseImageryProvider):
    """Simulates a provider that fetches Sentinel-2 imagery."""

    PROVIDER_NAME = "SENTINEL2"

    def query_imagery(
        self: "Sentinel2Provider",
        bbox: GEOSGeometry,
        start_date: datetime,
        end_date: datetime,
        cloud_cover_max: float = 100.0,
        resolution_max: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Simulate querying the Sentinel-2 API for imagery.

        Args:
            bbox: Spatial boundary to query.
            start_date: Start of capture date range.
            end_date: End of capture date range.
            cloud_cover_max: Max allowed cloud cover.
            resolution_max: Max desired resolution (unused in mock).

        Returns:
            A list of mocked image metadata dictionaries.
        """
        print(
            f"MOCK Sentinel2: Querying for bbox={bbox.wkt}, "
            f"dates={start_date.date()} to {end_date.date()}, "
            f"cloud_cover_max={cloud_cover_max}"
        )

        results = []
        num_images = random.randint(1, 3)

        for _ in range(num_images):
            time_difference = end_date - start_date
            random_seconds = random.randint(0, int(time_difference.total_seconds()))
            capture_date = start_date + timedelta(seconds=random_seconds)

            if capture_date.tzinfo is None:
                capture_date = pytz.utc.localize(capture_date)
            else:
                capture_date = capture_date.astimezone(pytz.utc)

            min_x, min_y, max_x, max_y = bbox.extent

            p1_x = min_x + random.uniform(0, (max_x - min_x) * 0.1)
            p1_y = min_y + random.uniform(0, (max_y - min_y) * 0.1)

            footprint_polygon = Polygon(
                (
                    (p1_x, p1_y),
                    (
                        min_x + random.uniform(0, (max_x - min_x) * 0.1),
                        min_y + random.uniform(0, (max_y - min_y) * 0.1),
                    ),
                    (
                        min_x + random.uniform(0, (max_x - min_x) * 0.1),
                        max_y - random.uniform(0, (max_y - min_y) * 0.1),
                    ),
                    (
                        max_x - random.uniform(0, (max_x - min_x) * 0.1),
                        max_y - random.uniform(0, (max_y - min_y) * 0.1),
                    ),
                    (
                        max_x - random.uniform(0, (max_x - min_x) * 0.1),
                        min_y + random.uniform(0, (max_y - min_y) * 0.1),
                    ),
                    (
                        min_x + random.uniform(0, (max_x - min_x) * 0.1),
                        min_y + random.uniform(0, (max_y - min_y) * 0.1),
                    ),
                    (p1_x, p1_y),
                ),
                srid=4326,
            )

            dummy_meta = {
                "id": f"S2_MOCK_{capture_date.strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
                "type": "Feature",
                "properties": {
                    "cloud_cover": min(random.uniform(0, cloud_cover_max + 5), 100.0),
                    "acquisition_date": capture_date.isoformat(),
                    "resolution_in_meters": random.choice([10.0, 20.0]),
                    "product_type": "S2MSI2A",
                    "tile_id": "MOCK_TILE_" + str(random.randint(1, 100)),
                    "download_link": (
                        f"http://mock-sentinel2-data.com/images/s2_"
                        f"{capture_date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}.tiff"
                    ),
                },
                "geometry": json.loads(footprint_polygon.geojson),
            }
            results.append(dummy_meta)

        return results

    def get_image_details(self: "Sentinel2Provider", image_id: str) -> Dict[str, Any]:
        """
        Simulate retrieving metadata for a specific Sentinel-2 image.

        Args:
            image_id: The ID of the image.

        Returns:
            A dictionary representing the image metadata.
        """
        print(f"MOCK Sentinel2: Getting details for image_id={image_id}")

        now_utc_aware = pytz.utc.localize(datetime.now())
        return {
            "id": image_id,
            "properties": {
                "acquisition_date": now_utc_aware.isoformat(),
                "resolution_in_meters": 10.0,
                "cloud_cover": 5.0,
                "download_link": f"http://mock.com/image/{image_id}.tiff",
            },
            "geometry": json.loads(
                Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)), srid=4326).geojson
            ),
        }

    def get_image_file_data(self: "Sentinel2Provider", image_url: str) -> bytes:
        """
        Simulate retrieving raw image byte data from a URL.

        Args:
            image_url: The mock image URL.

        Returns:
            A byte string representing fake image content.
        """
        print(f"MOCK Sentinel2: Retrieving raw data for {image_url}")
        return b"This is a dummy satellite image file content for Jenga. It's not a real image."

    def parse_api_metadata(
        self: "Sentinel2Provider", raw_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse mock API metadata into a standardized format.

        Args:
            raw_metadata: Raw metadata dictionary from the mock provider.

        Returns:
            Parsed metadata dictionary matching SatelliteImage model format.
        """
        properties = raw_metadata.get("properties", {})
        geometry_data = raw_metadata.get("geometry", {})

        date_captured_str = properties.get("acquisition_date")
        date_captured: Optional[datetime] = None

        if date_captured_str:
            try:
                parsed_dt_naive = datetime.fromisoformat(date_captured_str)
                if parsed_dt_naive.tzinfo is None:
                    date_captured = pytz.utc.localize(parsed_dt_naive)
                else:
                    date_captured = parsed_dt_naive.astimezone(pytz.utc)
            except ValueError:
                print(
                    f"Warning: Could not parse acquisition_date '{date_captured_str}'. "
                    "Falling back to current UTC time."
                )
                date_captured = django_timezone.now()
        else:
            date_captured = django_timezone.now()

        footprint_geojson = json.dumps(geometry_data)
        footprint = GEOSGeometry(footprint_geojson, srid=4326)

        return {
            "date_captured": date_captured,
            "resolution_m_per_pixel": properties.get("resolution_in_meters"),
            "source": self.PROVIDER_NAME,
            "cloud_cover_percentage": properties.get("cloud_cover"),
            "footprint": footprint,
            "metadata": raw_metadata,
        }
