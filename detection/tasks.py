"""Celery tasks for processing satellite imagery and detecting changes."""

from celery import shared_task
from celery.app.task import Task  # Import Task for type hinting 'self'
from django.db import transaction
from django.shortcuts import get_object_or_404

# from django.utils import timezone as django_timezone  # Removed: F401 unused import

# Import models
from core.models import SatelliteImage, Site  # Import Site model for ChangeLog
from detection.models import Detection, ChangeLog  # Import ChangeLog

# Import the AI client
from detection.client import AIMicroserviceClient

# import pytz  # Removed: F401 unused import
# from datetime import datetime # Removed: F401 unused import


# --- Task for AI processing (existing, just updated trigger) ---
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_detections(self: Task, satellite_image_id: int) -> str:
    """Celery task to send a SatelliteImage to the AI microservice for detection.

    Stores the results.
    """
    try:
        satellite_image = get_object_or_404(SatelliteImage, id=satellite_image_id)
        print(
            f"Processing SatelliteImage: {satellite_image.pk} "
            f"(Site: {satellite_image.site.name}) for AI detections."
        )

        ai_client = AIMicroserviceClient()
        mock_image_url_for_ai = (
            f"http://internal-storage.com/images/{satellite_image.pk}.tiff"
        )
        raw_detection_results = ai_client.send_image_for_inference(
            mock_image_url_for_ai
        )

        detections_count = 0
        if not raw_detection_results:
            print(f"No objects detected in SatelliteImage {satellite_image.pk}.")
        else:
            for raw_result in raw_detection_results:
                try:
                    parsed_data = ai_client.parse_ai_response(raw_result)
                    with transaction.atomic():
                        Detection.objects.create(
                            satellite_image=satellite_image,
                            detected_class=parsed_data["detected_class"],
                            coordinates=parsed_data["coordinates"],
                            confidence=parsed_data["confidence"],
                            location=parsed_data["location"],
                            timestamp=parsed_data["timestamp"],
                            metadata=parsed_data["metadata"],
                        )
                        detections_count += 1
                        print(
                            f"  - Created Detection: {parsed_data['detected_class']} "
                            f"(Confidence: {parsed_data['confidence']})"
                        )
                except Exception as e:
                    print(
                        f"Error parsing/creating detection for image "
                        f"{satellite_image.pk}: {e}"
                    )
                    continue

        satellite_image.status = "PROCESSED"
        satellite_image.save(update_fields=["status"])

        print(
            f"Successfully processed SatelliteImage {satellite_image.pk} and created "
            f"{detections_count} detections. Triggering change detection."
        )

        # --- CRITICAL ADDITION: Trigger change detection task ---
        # Trigger the change detection task for this site after image processing
        detect_site_changes.delay(site_id=satellite_image.site.id)
        # ----------------------------------------------------

        return (
            f"Processed image {satellite_image.pk}: " f"{detections_count} detections."
        )

    except SatelliteImage.DoesNotExist:
        print(
            f"Error: SatelliteImage with ID {satellite_image_id} does not exist. "
            "Aborting task."
        )
        raise

    except Exception as e:
        print(
            f"An unexpected error occurred processing image {satellite_image_id}: {e}"
        )
        self.retry(exc=e)


# --- NEW TASK: Change Detection Logic ---
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def detect_site_changes(self: Task, site_id: int) -> str:
    """Celery task to detect changes on a site.

    Compares the latest two processed satellite images and their detections.
    """
    try:
        site = get_object_or_404(Site, id=site_id)
        print(f"Detecting changes for Site: {site.name} ({site.id})")

        # 1. Identify the latest two PROCESSED SatelliteImage records for the site.
        # Ensure they are ordered by date_captured descending.
        latest_images = SatelliteImage.objects.filter(
            site=site,
            status="PROCESSED",  # Only consider images that have been processed
        ).order_by("-date_captured")[
            :2
        ]  # Get the top 2 most recent

        if len(latest_images) < 2:
            print(
                f"Not enough processed images for site {site.name} to perform change "
                f"detection (found {len(latest_images)})."
            )
            return "Insufficient images for change detection."

        image_after = latest_images[0]  # Most recent image
        image_before = latest_images[1]  # Second most recent image

        print(
            f"Comparing Image: {image_before.pk} (Captured: "
            f"{image_before.date_captured.date()}) "
            f"with Image: {image_after.pk} (Captured: "
            f"{image_after.date_captured.date()})"
        )

        # 2. Retrieve all Detection objects for both images.
        detections_before = Detection.objects.filter(
            satellite_image=image_before
        ).count()
        detections_after = Detection.objects.filter(satellite_image=image_after).count()

        change_type = "NO_CHANGE"
        description = "No significant change detected."
        metadata = {
            "image_before_id": image_before.pk,
            "image_after_id": image_after.pk,
            "detections_before_count": detections_before,
            "detections_after_count": detections_after,
            "change_details": {},  # Placeholder for more detailed diff
        }

        # 3. Implement basic comparison logic (e.g., based on count of detections)
        if detections_after > detections_before:
            change_type = "NEW_DETECTIONS"
            description = (
                f"New objects detected: {detections_after - detections_before} "
                "more objects than previous image."
            )
        elif detections_after < detections_before:
            change_type = "REMOVED_DETECTIONS"
            description = (
                f"Objects removed: {detections_before - detections_after} "
                "fewer objects than previous image."
            )
        elif detections_after == 0 and detections_before == 0:
            change_type = "NO_CHANGE"
            description = "No objects detected in either image."
        else:  # counts are equal but not zero, or other subtle changes
            # This is where more complex geospatial comparison would go
            # (e.g., Intersection over Union).
            # For now, if counts are equal but not zero, we'll mark as no
            # major count change.
            change_type = (
                "COUNT_CHANGED"
                if detections_after != detections_before
                else "NO_CHANGE"
            )
            description = (
                f"Detection count is {detections_after}. "
                "No significant change in count."
            )

        # 4. Generate ChangeLog entries based on identified differences.
        with transaction.atomic():
            ChangeLog.objects.create(  # Renamed to _change_log
                site=site,
                image_before=image_before,
                image_after=image_after,
                change_type=change_type,
                description=description,
                metadata=metadata,
            )
            print(
                f"Created ChangeLog for site {site.name}: "
                f"Type='{change_type}', Description='{description}'"
            )

        return (
            f"Change detection completed for site {site.name}. "
            f"Change Type: {change_type}."
        )

    except Site.DoesNotExist:
        print(
            f"Error: Site with ID {site_id} does not exist for change detection. "
            "Aborting task."
        )
        raise

    except Exception as e:
        print(
            f"An unexpected error occurred during change detection for site "
            f"{site_id}: {e}"
        )
        self.retry(exc=e)
