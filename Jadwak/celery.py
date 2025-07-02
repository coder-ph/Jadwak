"""Celery configuration for Jadwak project."""

from celery import Celery, Task

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jadwak.settings")

app = Celery("jadwak")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self: Task) -> None:
    """Print the request information for debugging purposes."""
    print(f"Request: {self.request!r}")
