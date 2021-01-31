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
    fields = ["uuid", "type", "source_account", "destination_account", "amount", "foreign_amount", "created", "modified"]
    readonly_fields = fields


@admin.register(models.TransactionJournal)
class TransactionJournalAdmin(admin.ModelAdmin):
    ordering = ["date"]
    date_hierarchy = "date"
    list_display = ["uuid", "short_description", "date", "created", "modified"]
    search_fields = ["uuid", "short_description", "description"]
    fieldsets = [["General information", {"fields": ["date", "short_description", "description"]}], ["Options", {"fields": ["uuid"]}]]
    readonly_fields = ["uuid"]
    inlines = [TransactionInline]


@admin.register(models.Account)
@admin.register(models.CashAccount)
class AccountAdmin(admin.ModelAdmin):
    ordering = ["name"]
    list_display = [
        "name",
        "slug",
        "type",
        "icon",
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
    search_fields = ["name", "uuid"]
    fieldsets = [
        ["General information", {"fields": ["name", "slug", "type", "icon", "currency"]}],
        ["Options", {"fields": ["active", "net_worth", "dashboard", "virtual_balance", "uuid"]}],
    ]
    readonly_fields = ["slug", "type", "icon", "uuid"]


@admin.register(models.AssetAccount)
@admin.register(models.ExpenseAccount)
@admin.register(models.RevenueAccount)
class IBANAccountAdmin(AccountAdmin):
    def display_iban(self, obj):
        return format_iban(obj.iban)

    display_iban.short_description = "IBAN"

    def get_list_display(self, request):
        list_display = self.list_display.copy()
        list_display.insert(2, "display_iban")

        return list_display

    def get_search_fields(self, request):
        search_fields = self.search_fields.copy()
        search_fields.append("iban")

        return search_fields

    fieldsets = [
        ["General information", {"fields": ["name", "iban", "slug", "type", "icon", "currency"]}],
        ["Options", {"fields": ["active", "net_worth", "dashboard", "virtual_balance", "uuid"]}],
    ]


@admin.register(models.LiabilitiesAccount)
class NumberAccountAdmin(AccountAdmin):
    def get_list_display(self, request):
        list_display = self.list_display.copy()
        list_display.insert(2, "account_number")

        return list_display

    def get_search_fields(self, request):
        search_fields = self.search_fields.copy()
        search_fields.append("account_number")

        return search_fields

    fieldsets = [
        ["General information", {"fields": ["name", "account_number", "slug", "type", "icon", "currency"]}],
        ["Options", {"fields": ["active", "net_worth", "dashboard", "virtual_balance", "uuid"]}],
    ]