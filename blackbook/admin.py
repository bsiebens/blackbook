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


class TransactionInline(admin.TabularInline):
    model = models.Transaction
    extra = 0
    fields = ["uuid", "account", "amount", "foreign_amount", "created", "modified"]
    readonly_fields = fields


@admin.register(models.TransactionJournal)
class TransactionJournalAdmin(admin.ModelAdmin):
    ordering = ["date"]
    date_hierarchy = "date"
    list_display = ["uuid", "short_description", "date", "amount", "type", "created", "modified"]
    search_fields = ["uuid", "short_description", "description"]
    fieldsets = [
        [
            "General information",
            {"fields": ["date", "short_description", "description", "type"]},
        ],
        ["Options", {"fields": ["uuid"]}],
    ]
    list_filter = ["type"]
    readonly_fields = ["uuid"]
    inlines = [TransactionInline]


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    def display_iban(self, obj):
        return format_iban(obj.iban)

    display_iban.short_description = "IBAN"

    ordering = ["name"]
    list_display = [
        "name",
        "slug",
        "type",
        "display_iban",
        "currency",
        "active",
        "net_worth",
        "dashboard",
        "virtual_balance",
        "balance",
        "uuid",
        "created",
        "modified",
    ]
    list_filter = ["type", "active", "net_worth", "dashboard", "currency"]
    search_fields = ["name", "uuid", "iban"]
    fieldsets = [
        ["General information", {"fields": ["name", "iban", "slug", "type", "icon", "currency"]}],
        ["Options", {"fields": ["active", "net_worth", "dashboard", "virtual_balance", "uuid"]}],
    ]
    readonly_fields = ["slug", "icon", "uuid"]


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    ordering = ["name"]
    list_display = ["name", "uuid", "created", "modified"]
    search_fields = ["name"]
    fieldsets = [
        ["General information", {"fields": ["name", "uuid"]}],
    ]
    readonly_fields = ["uuid"]