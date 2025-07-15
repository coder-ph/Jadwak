"""Celery tasks for image processing and Sentinel-2 imagery fetching."""

import time
from datetime import datetime

import pytz
from celery import Task, shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from core.models import SatelliteImage, Site
from core.providers.imagery.sentinel2 import Sentinel2Provider

from detection.tasks import process_image_detections


@shared_task
def example_task(arg1: int, arg2: str) -> int:
    """Simulate a long-running task and return a computed value."""
    start_time = timezone.now()
    print(f"Task started at {start_time} with arguments: {arg1}, {arg2}")
    time.sleep(5)
    end_time = timezone.now()
    print(f"Task ended at {end_time}")
    duration = (end_time - start_time).total_seconds()
    print(f"Task duration: {duration} seconds")
    return arg1 + len(arg2)


@shared_task
def another_example_task() -> None:
    """Run a dummy task that simply waits."""
    print(
        f"This is another example task that does nothing. Running at {timezone.now()}"
    )
    time.sleep(2)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_sentinel2_imagery(
    self: Task, site_id: int, start_date_str: str, end_date_str: str
) -> str:
    """Fetch Sentinel-2 imagery for a given site and date range."""
    try:
        site = Site.objects.get(id=site_id)

        start_date = pytz.utc.localize(datetime.fromisoformat(start_date_str))
        end_date = pytz.utc.localize(datetime.fromisoformat(end_date_str))

        print(
            f"Fetching Sentinel-2 imagery for Site: {site.name} ({site.id}) "
            f"from {start_date.date()} to {end_date.date()}"
        )

        provider = Sentinel2Provider()

        imagery_results = provider.query_imagery(
            bbox=site.boundary,
            start_date=start_date,
            end_date=end_date,
            cloud_cover_max=20.0,
        )

        if not imagery_results:
            print(
                f"No Sentinel-2 imagery found for site {site.name} in the specified date range and criteria."
            )
            return "No imagery found."

        fetched_count = 0
        for result in imagery_results:
            try:
                parsed_data = provider.parse_api_metadata(result)
                dummy_image_content_bytes = provider.get_image_file_data(
                    parsed_data.get("metadata", {})
                    .get("properties", {})
                    .get("download_link", "")
                )

                with transaction.atomic():
                    satellite_image = SatelliteImage.objects.create(
                        site=site,
                        image_file=ContentFile(
                            dummy_image_content_bytes,
                            name=f"{site.name.replace(' ', '_')}_S2_"
                            f"{parsed_data['date_captured'].strftime('%Y%m%d_%H%M%S')}.tiff",
                        ),
                        date_captured=parsed_data["date_captured"],
                        resolution_m_per_pixel=parsed_data["resolution_m_per_pixel"],
                        source=parsed_data["source"],
                        cloud_cover_percentage=parsed_data["cloud_cover_percentage"],
                        footprint=parsed_data["footprint"],
                        metadata=parsed_data["metadata"],
                        status="FETCHED",
                    )
                    fetched_count += 1
                    print(
                        f"Successfully created SatelliteImage: {satellite_image.pk} "
                        f"for site {site.name}. Triggering AI processing"
                    )
                    process_image_detections.delay(satellite_image.pk)

            except Exception as e:
                print(
                    f"Error processing a SatelliteImage result for site {site.name}: {e}"
                )
                continue

        return f"Successfully fetched and processed {fetched_count} images for site {site.name}."

    except Site.DoesNotExist:
        print(f"Error: Site with ID {site_id} does not exist. Aborting task.")
        raise

    except Exception as e:
        print(
            f"An unexpected error occurred while fetching Sentinel-2 imagery for site {site_id}: {e}"
        )
        self.retry(exc=e)
