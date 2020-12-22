from django.contrib import admin

from taggit_helpers.admin import TaggitListFilter

from . import models
from .utilities import format_iban


class BudgetPeriodInline(admin.TabularInline):
    model = models.BudgetPeriod
    extra = 0
    fields = ("start_date", "end_date", "amount", "created", "modified")
    readonly_fields = ("start_date", "end_date", "amount", "created", "modified")


class TransactionInline(admin.TabularInline):
    model = models.Transaction
    extra = 0
    fields = ("account", "amount", "reconciled", "created", "modified")
    readonly_fields = ("amount", "reconciled", "created", "modified")


@admin.register(models.AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    ordering = ["name"]
    list_display = ["name", "icon", "slug", "created", "modified"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug"]


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    def display_iban(self, obj):
        return format_iban(obj.iban)

    display_iban.short_description = "IBAN"

    ordering = ["name"]
    list_display = [
        "name",
        "slug",
        "account_type",
        "currency",
        "display_iban",
        "active",
        "include_in_net_worth",
        "virtual_balance",
        "balance",
        "uuid",
        "created",
        "modified",
    ]
    list_filter = ["account_type", "user", "active", "include_in_net_worth", "currency"]
    search_fields = ["name", "iban", "uuid"]
    fieldsets = (
        ("General information", {"fields": ("name", "slug", "user", "account_type", "iban", "currency")}),
        ("Options", {"fields": ("active", "include_in_net_worth", "virtual_balance", "uuid")}),
    )
    raw_id_fields = ["user"]
    readonly_fields = ["slug", "uuid"]


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    ordering = ["name"]
    list_display = ["name", "user", "uuid", "created", "modified"]
    search_fields = ["name"]
    raw_id_fields = ["user"]
    fieldsets = (
        ("General information", {"fields": ("name", "user")}),
        ("Options", {"fields": ("uuid",)}),
    )
    readonly_fields = ["uuid"]


@admin.register(models.Budget)
class BudgetAdmin(admin.ModelAdmin):
    ordering = ["name"]
    list_display = ["name", "user", "active", "amount", "auto_budget", "auto_budget_period", "uuid", "created", "modified"]
    search_fields = ["name", "uuid"]
    list_filter = ["active", "auto_budget", "auto_budget_period"]
    fieldsets = (
        ("General information", {"fields": ("name", "user")}),
        ("Options", {"fields": ("active", "amount", "auto_budget", "auto_budget_period", "uuid")}),
    )
    inlines = [BudgetPeriodInline]
    raw_id_fields = ["user"]
    readonly_fields = ["uuid"]


@admin.register(models.TransactionJournalEntry)
class TransactionJournalEntryAdmin(admin.ModelAdmin):
    def show_tags(self, obj):
        return ", ".join([tag.name.lower() for tag in obj.tags.all()])

    show_tags.short_description = "tags"

    ordering = ["-date"]
    date_hierarchy = "date"
    list_display = [
        "description",
        "user",
        "date",
        "transaction_type",
        "amount",
        "category",
        "show_tags",
        "budget",
        "from_account",
        "to_account",
        "uuid",
        "created",
        "modified",
    ]
    list_filter = ["transaction_type", "category", "budget", TaggitListFilter]
    search_fields = ["description", "uuid"]
    fieldsets = (
        ("General information", {"fields": ("description", "user", "date", "transaction_type", "amount")}),
        ("Options", {"fields": ("budget", "category", "tags", "uuid")}),
    )
    readonly_fields = ["uuid"]
    inlines = [TransactionInline]
    raw_id_fields = ["user"]


@admin.register(models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["account", "amount", "negative", "reconciled", "uuid", "created", "modified"]
    list_filter = ["account", "reconciled"]
    raw_id_fields = ["journal_entry"]
    fieldsets = (
        ("General information", {"fields": ("account", "amount", "journal_entry")}),
        ("Options", {"fields": ("negative", "reconciled", "uuid")}),
    )
    readonly_fields = ["uuid"]


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    def get_name(self, obj):
        return obj.user.get_full_name()

    get_name.short_description = "Full name"

    list_display = ["user", "get_name", "default_currency", "default_period", "created", "modified"]
    ordering = ["user"]
    search_fields = ["user", "uuid"]
    raw_id_fields = ["user"]
    fieldsets = (("General information", {"fields": ("user", "default_currency", "default_period")}),)
