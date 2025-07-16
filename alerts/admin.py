"""register alerts to admin."""

from django.contrib import admin
from .models import Alert, AlertRule


# Register your models here.
@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """admin interface for the Alert model."""

    list_display = ("type", "site", "user", "triggered_on", "status", "change_log")
    list_filter = ("type", "status", "site", "triggered_on")
    search_fields = ("description", "site__name", "type", "user__username")
    raw_id_fields = ("site", "user", "change_log")
    readonly_fields = ("triggered_on",)


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """admin interface for the AlertRule model."""

    list_display = ("site", "rule_type", "is_active", "threshold", "target_class")
    list_filter = ("rule_type", "is_active", "site")
    search_fields = ("site__name", "rule_type", "target_class")
    raw_id_fields = ("site",)
    list_editable = ("is_active",)
