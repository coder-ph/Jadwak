"""
WSGI config for jenga_platform project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""


from django.core.wsgi import get_wsgi_application

# Check for DJANGO_SETTINGS_MODULE environment variable
# If not set, default to production settings (as WSGI is typically for production)
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Jadwak.settings.prod")

application = get_wsgi_application()
