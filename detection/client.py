"""Client for the AI microservice in the detection application."""

import json
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz
from django.conf import settings  # Re-introducing settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.utils import timezone  # Re-introducing timezone


class AIMicroserviceClient:
    """Client for interacting with the AI microservice.

    This is a mock client for an external AI Microservice (e.g., Flask/FastAPI
    running YOLOv8/Faster R-CNN). In a real scenario, this would make HTTP
    requests to the actual AI service.
    """

    def __init__(self: "AIMicroserviceClient", base_url: Optional[str] = None) -> None:
        """Initialize the client with the base URL of the AI microservice."""
        # Use settings for base_url in a real scenario, mock for development
        self.base_url = base_url or getattr(
            settings, "AI_MICROSERVICE_URL", "http://mock-ai-service.com/inference"
        )
        # In a real scenario:
        # self.headers = {"Authorization": f"Bearer {settings.AI_SERVICE_API_KEY}"}

    def send_image_for_inference(
        self: "AIMicroserviceClient",
        image_url: str,
    ) -> List[Dict[str, Any]]:
        """Send an image URL to the AI microservice for inference.

        This method simulates sending an image and receiving detection results.
        """
        # In a real scenario, this would be an HTTP POST request to the AI service
        print(f"Sending image {image_url} for inference to {self.base_url}")

        # Simulate network delay
        time.sleep(random.uniform(0.5, 2.0))
        detected_objects = []
        num_detections = random.randint(0, 5)

        # Simulate detections
        for _ in range(num_detections):  # Changed 'i' to '_'
            detected_class = random.choice(
                ["EXCAVATOR", "CRANE", "TRUCK", "GRADER", "BULLDOZER"]
            )
            confidence = round(random.uniform(0.6, 0.99), 2)

            # Simulate bounding box coordinates (pixel values)
            x1 = random.randint(0, 800)
            y1 = random.randint(0, 800)
            x2 = x1 + random.randint(50, 200)
            y2 = y1 + random.randint(50, 200)
            bbox_pixels = [x1, y1, x2, y2]  # Renamed for clarity

            # Simulate a geographic location (Point) for the detection
            # This would be derived from image coordinates and geo-referencing
            # in a real scenario. For mock, we'll just generate a random point
            # near Nairobi.
            mock_lon = random.uniform(36.7, 36.9)
            mock_lat = random.uniform(-1.35, -1.2)
            location_point = Point(mock_lon, mock_lat, srid=4326)

            detection_result = {
                "class": detected_class,
                "confidence": confidence,
                "bbox_pixels": bbox_pixels,  # Use the new name
                "geo_location": json.loads(
                    location_point.geojson
                ),  # GeoJSON representation
                "timestamp_utc": datetime.now(pytz.utc).isoformat(),  # Use pytz.utc
                "model_version": "YOLOv8-Mock-v1.0",
            }
            detected_objects.append(detection_result)

        print(f"MOCK AI Service: Detected {num_detections} objects.")
        return detected_objects

    def parse_ai_response(
        self: "AIMicroserviceClient", raw_detection_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse raw detection data from the AI service into a standardized format."""
        detected_class = raw_detection_data.get("class", "unknown")
        confidence = raw_detection_data.get("confidence", 0.0)
        # 'coordinates' variable removed as it was unused.
        # If bbox_pixels are needed, they will be part of metadata.
        bbox_pixels_from_raw = raw_detection_data.get("bbox_pixels", [])

        geo_location_geojson = json.dumps(raw_detection_data.get("geo_location", {}))
        location = GEOSGeometry(geo_location_geojson, srid=4326)

        timestamp_str = raw_detection_data.get(
            "timestamp_utc", datetime.now(pytz.utc).isoformat()
        )
        if timestamp_str:
            parsed_dt_naive = datetime.fromisoformat(timestamp_str)
            timestamp = pytz.utc.localize(parsed_dt_naive)
        else:
            # Fallback to Django's now() if timestamp_str is empty or invalid
            timestamp = timezone.now()

        # Include bbox_pixels in metadata if desired, or omit if not needed downstream
        metadata = raw_detection_data.get("metadata", {})
        metadata["bbox_pixels"] = bbox_pixels_from_raw  # Add bbox_pixels to metadata

        return {
            "detected_class": detected_class,
            "confidence": confidence,
            "location": location,
            "timestamp": timestamp,
            "metadata": metadata,  # Now includes bbox_pixels
            "model_version": raw_detection_data.get("model_version", "unknown"),
        }
