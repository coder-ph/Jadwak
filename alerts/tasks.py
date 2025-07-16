"""Contains celery tasks for generating and sending alerts."""

import json
import requests

from typing import List

from celery import shared_task
from celery.app.task import Task  # Import Task for type hinting 'self'
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags

from alerts.models import Alert
from detection.models import ChangeLog

from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_alerts(self: Task, change_log_id: int) -> str:
    """Celery task to generate alerts based on a ChangeLog entry."""
    try:
        change_log = get_object_or_404(ChangeLog, id=change_log_id)
        site = change_log.site

        print(
            f"Generating alerts for ChangeLog {change_log.pk} on Site: {site.name} "
            f"(Type: {change_log.change_type})."
        )

        # --- SIMPLIFIED / HARDCODED ALERT RULE APPLICATION ---
        # In a real scenario, you would query AlertRule.objects.filter(site=site, is_active=True)
        # and evaluate each rule against the change_log's data.
        # For now, we'll use direct if/else based on change_type.

        alert_type = "OTHER"
        description = change_log.description
        trigger_alert = True

        if change_log.change_type == "NEW_DETECTIONS":
            alert_type = "NEW_EQUIPMENT_DETECTED"
            description = (
                f"New equipment detected on site {site.name}: {change_log.description}"
            )
        elif change_log.change_type == "REMOVED_DETECTIONS":
            alert_type = "EQUIPMENT_MISSING"
            description = (
                f"Equipment removed from site {site.name}: {change_log.description}"
            )
        elif change_log.change_type == "SITE_ACTIVITY_HIGH":
            alert_type = "SITE_ACTIVITY_HIGH"
            description = (
                f"High activity detected on site {site.name}: {change_log.description}"
            )
        elif change_log.change_type == "SITE_ACTIVITY_LOW":
            alert_type = "SITE_ACTIVITY_LOW"
            description = (
                f"Low activity detected on site {site.name}: {change_log.description}"
            )
        elif change_log.change_type == "COUNT_CHANGED":
            alert_type = "COUNT_THRESHOLD_EXCEEDED"
            description = (
                f"Detection count changed on site {site.name}: {change_log.description}"
            )
        else:
            trigger_alert = (
                False  # Don't create an alert for 'NO_CHANGE' or unhandled types
            )

        if trigger_alert:
            # Create Alert instance
            with transaction.atomic():
                # For simplicity, link to the site's owner for now.
                # In Sprint 5, users can subscribe to alerts.
                alert = Alert.objects.create(
                    type=alert_type,
                    site=site,
                    user=site.owner,  # Link to site owner as the recipient for now
                    change_log=change_log,
                    description=description,
                    metadata=change_log.metadata,  # Pass change_log metadata to alert
                )
                print(f"Created Alert {alert.pk} for site {site.name}: '{description}'")

                # Trigger notification tasks
                send_email_alert.delay(alert.pk)
                send_webhook_alert.delay(alert.pk)

            return (
                f"Alert generated for ChangeLog {change_log.pk} "
                f"(Type: {alert_type}). Notifications triggered."
            )
        else:
            print(
                "No alert generated for ChangeLog "
                f"{change_log.pk} based on current rules."  # Fixed F541
            )
            return f"No alert for ChangeLog {change_log.pk}."

    except ChangeLog.DoesNotExist:
        print(
            f"Error: ChangeLog with ID {change_log_id} does not exist. "
            "Aborting alert generation task."
        )
        raise
    except Exception as e:
        print(
            f"An unexpected error occurred during alert generation for ChangeLog "
            f"{change_log_id}: {e}"
        )
        self.retry(exc=e)


# --- Notification Tasks ---
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_email_alert(self: Task, alert_id: int) -> str:
    """Celery task to send an email notification for a triggered alert."""
    try:
        alert = get_object_or_404(Alert, id=alert_id)
        recipient_list: List[str] = []  # Explicitly type hint List[str]
        if alert.user and alert.user.email:
            recipient_list.append(alert.user.email)
        elif alert.site.owner and alert.site.owner.email:
            recipient_list.append(alert.site.owner.email)

        if not recipient_list:
            print(f"No email recipients for alert {alert.pk}.")
            return f"No email recipients for alert {alert.pk}."

        subject = f"Jenga Alert: {alert.get_type_display()} on {alert.site.name}"
        message = alert.description
        html_message = (
            f"<p><strong>Jenga Platform Alert!</strong></p>"
            f"<p><strong>Site:</strong> {alert.site.name}</p>"
            f"<p><strong>Type:</strong> {alert.get_type_display()}</p>"
            f"<p><strong>Description:</strong> {message}</p>"
            f"<p><strong>Triggered On:</strong> {alert.triggered_on.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>"
            f'<p>View on Jenga dashboard: <a href="http://localhost:8001/admin/alerts/alert/{alert.pk}/change/">'
            "View Alert (Dev Admin)</a></p>"  # Line break for E501
            "<p>Best regards,<br>The Jenga Team</p>"
        )
        plain_message = strip_tags(html_message)

        # Mock email sending for now (print to console)
        print("\n--- MOCK EMAIL ALERT ---")  # Fixed F541
        print(f"To: {', '.join(recipient_list)}")
        print(f"Subject: {subject}")
        print(f"Body (HTML): {html_message}")
        print("--- END MOCK EMAIL ALERT ---\n")  # Fixed F541

        # In a real scenario, you'd use Django's send_mail:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,  # Must be configured in settings
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        return f"Mock email sent for Alert {alert.pk} to {recipient_list}."

    except Alert.DoesNotExist:
        print(f"Error: Alert with ID {alert_id} does not exist for email notification.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred sending email for Alert {alert_id}: {e}")
        self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_webhook_alert(self: Task, alert_id: int) -> str:
    """Celery task to send a webhook notification for a triggered alert."""
    try:
        alert = get_object_or_404(Alert, id=alert_id)

        # --- MOCK WEBHOOK URL ---
        # In a real scenario, this would come from AlertRule config or Integration settings
        webhook_url = "http://mock-webhook-receiver.com/alert"
        # ------------------------

        payload = {
            "alert_id": alert.pk,
            "type": alert.type,
            "site_id": alert.site.id,
            "site_name": alert.site.name,
            "description": alert.description,
            "timestamp": alert.triggered_on.isoformat(),
            "status": alert.status,
            "metadata": alert.metadata,
        }

        # Mock webhook sending for now (print to console)
        print("\n--- MOCK WEBHOOK ALERT ---")  # Fixed F541
        print(f"To: {webhook_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("--- END MOCK WEBHOOK ALERT ---\n")  # Fixed F541

        # In a real scenario, you'd use requests:
        # response = requests.post(webhook_url, json=payload, timeout=10)
        # response.raise_for_status() # Raise an exception for HTTP errors
        # print(f"Webhook sent successfully for Alert {alert.pk}. Response: {response.status_code}")

        return f"Mock webhook sent for Alert {alert.pk}."

    except Alert.DoesNotExist:
        print(
            f"Error: Alert with ID {alert_id} does not exist for webhook notification."
        )
        raise
    except (
        requests.exceptions.RequestException
    ) as e:  # Catch network/HTTP errors for real requests
        print(f"Network/HTTP error sending webhook for Alert {alert_id}: {e}")
        self.retry(exc=e)  # Retry for network errors
    except Exception as e:
        print(f"An unexpected error occurred sending webhook for Alert {alert_id}: {e}")
        self.retry(exc=e)
