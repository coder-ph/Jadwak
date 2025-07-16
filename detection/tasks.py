"""Celery tasks for processing satellite imagery and detecting changes."""

import random

from celery import shared_task
from celery.app.task import Task  # Import Task for type hinting 'self'
from django.db import transaction
from django.shortcuts import get_object_or_404


# Import models
from core.models import SatelliteImage, Site
from detection.models import Detection, ChangeLog
from alerts.tasks import generate_alerts


from detection.client import AIMicroserviceClient


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

        # Calling the (now unified) detect_site_changes task
        detect_site_changes.delay(
            site_id=satellite_image.site.id, processed_image_id=satellite_image.pk
        )

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


# --- Change Detection Logic (Unified and Corrected) ---
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def detect_site_changes(self: Task, site_id: int, processed_image_id: int) -> str:
    """Celery task to detect changes on a site.

    Compares detections between the newly processed image and a previous image.
    This is a simplified/mocked change detection.
    """
    try:
        site = get_object_or_404(Site, id=site_id)
        # Ensure processed_image is fetched directly for this task,
        # in case the task chain order changes or the image wasn't fully saved yet.
        processed_image = get_object_or_404(
            SatelliteImage, id=processed_image_id, site=site
        )

        print(
            f"Detecting changes for Site: {site.name} ({site.id}) "
            f"using image {processed_image.pk}."
        )

        # Find the most recent *processed* image captured *before* the current one.
        # This assumes images are processed in order, or we want to compare with the
        # immediate prior.
        previous_image = (
            SatelliteImage.objects.filter(
                site=site,
                status="PROCESSED",  # Only compare with processed images
                date_captured__lt=processed_image.date_captured,  # Images captured before
            )
            .exclude(pk=processed_image.pk)
            .order_by("-date_captured")
            .first()
        )

        if not previous_image:
            # If this is the first processed image for the site,
            # log it but no comparison possible.
            print(
                f"No previous processed image found for site {site.name}. "
                "No comparison made."
            )
            # Optionally create a "SITE_INITIALIZED" ChangeLog here.
            return f"No previous image for site {site.name}. Change detection skipped."

        print(
            f"Comparing Image: {previous_image.pk} (Captured: "
            f"{previous_image.date_captured.date()}) "
            f"with Image: {processed_image.pk} (Captured: "
            f"{processed_image.date_captured.date()})"
        )

        # --- SIMPLIFIED MOCK CHANGE DETECTION LOGIC ---
        current_detections_count = processed_image.detections.count()
        previous_detections_count = previous_image.detections.count()

        change_type = "NO_CHANGE"
        description = (
            "No significant change in detection count."  # Corrected F541, removed f""
        )
        metadata = {
            "image_before_id": previous_image.pk,
            "image_after_id": processed_image.pk,
            "detections_before_count": previous_detections_count,
            "current_detection_count": current_detections_count,
            "change_details": {},  # Placeholder for more detailed diff
        }

        if current_detections_count > previous_detections_count:
            change_type = "NEW_DETECTIONS"
            description = (
                f"Increased detections from {previous_detections_count} to "
                f"{current_detections_count}."
            )
        elif current_detections_count < previous_detections_count:
            change_type = "REMOVED_DETECTIONS"
            description = (
                f"Decreased detections from {previous_detections_count} to "
                f"{current_detections_count}."
            )
        elif (
            current_detections_count == previous_detections_count
            and current_detections_count > 0
        ):
            change_type = "NO_CHANGE"
            description = f"Detection count remains at {current_detections_count}."
        elif current_detections_count == 0 and previous_detections_count == 0:
            change_type = "NO_CHANGE"
            description = "No detections found in either image."
        # Optionally, add a random chance for "SITE_ACTIVITY_HIGH" to show varying results
        if random.random() < 0.2:  # 20% chance
            change_type = "SITE_ACTIVITY_HIGH"
            description = "Mock: High site activity detected (random)."
        elif random.random() < 0.1:  # 10% chance
            change_type = "SITE_ACTIVITY_LOW"
            description = "Mock: Low site activity detected (random)."

        # Store results in a ChangeLog model
        with transaction.atomic():
            change_log = ChangeLog.objects.create(
                site=site,
                image_before=previous_image,
                image_after=processed_image,
                change_type=change_type,
                description=description,
                metadata=metadata,
            )
            print(
                f"Created ChangeLog entry {change_log.pk}: '{description}'. "
                "Triggering alert generation."
            )

            # Trigger alert generation task
            generate_alerts.delay(change_log.pk)

        return (
            f"Change detection completed for site {site.name}. "
            f"Change Type: {change_type}. Alert generation initiated."
        )

    except Site.DoesNotExist:
        print(f"Error: Site with ID {site_id} does not exist for change detection.")
        raise
    except SatelliteImage.DoesNotExist:
        print(
            f"Error: Processed SatelliteImage with ID {processed_image_id} does not "
            f"exist or not linked to site {site_id}."
        )
        raise
    except Exception as e:
        print(
            f"An unexpected error occurred during change detection for site "
            f"{site_id}: {e}"
        )
        self.retry(exc=e)
