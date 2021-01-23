from django.contrib import admin

from . import models
from .utilities import format_iban


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    def get_name(self, obj):
        return obj.user.get_full_name()

    get_name.short_description = "Name"

    list_display = ["user", "get_name", "default_currency", "created", "modified"]
    ordering = ["user"]
    search_fields = ["user", "uuid"]
    raw_id_fields = ["user"]
    fieldsets = [
        ["General information", {"fields": ["user", "default_currency"]}],
    ]
