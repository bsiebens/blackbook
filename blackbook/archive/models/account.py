from django.db import models
from django.conf import settings
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.functional import cached_property

from localflavor.generic.models import IBANField
from djmoney.models.fields import CurrencyField
from djmoney.money import Money
from decimal import Decimal

from .base import get_default_currency, get_default_value, get_currency_choices
from ..utilities import calculate_period, unique_slugify

import uuid


class AccountType(models.Model):
    class AccountTypeCategory(models.TextChoices):
        ASSETS = "assets", "Assets"
        LIABILITIES = "liabilities", "Liabilities"
        EXPENSES = "expenses", "Expenses"
        INCOME = "income", "Income"

    name = models.CharField(max_length=250)
    icon = models.CharField(max_length=250, default="fa-coins")
    slug = models.SlugField()
    category = models.CharField(max_length=250, choices=AccountTypeCategory.choices, default=AccountTypeCategory.ASSETS)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(AccountType, self).save(*args, **kwargs)


class Account(models.Model):
    name = models.CharField(max_length=250)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, related_name="accounts")
    active = models.BooleanField("active?", default=True)
    include_in_net_worth = models.BooleanField(
        "include in net worth?", default=True, help_text="Include this account when calculating total net worth?"
    )
    include_on_dashboard = models.BooleanField("include on dashboard?", default=True, help_text="Include this account on the graph on the frontpage?")
    iban = IBANField("IBAN", null=True, blank=True)
    currency = CurrencyField(default=get_default_currency(), choices=get_currency_choices())
    virtual_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.0,
        help_text="Enter a number here to have BlackBook treat this as the new zero point for this account. Leave at 0.0 to disable.",
    )
    slug = models.SlugField()
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(Account, self).save(*args, **kwargs)

    @cached_property
    def starting_balance(self):
        try:
            from .transaction import TransactionJournalEntry, Transaction

            opening_balance = (
                self.transactions.select_related("journal_entry")
                .filter(journal_entry__transaction_type=TransactionJournalEntry.TransactionType.START)
                .get(journal_entry__date=self.created)
            )

            return opening_balance.journal_entry.amount

        except Transaction.DoesNotExist:
            return Money(0, self.currency)

    @cached_property
    def balance(self):
        return self.balance_until_date()

    def balance_until_date(self, date=timezone.localdate()):
        total = self.transactions.filter(journal_entry__date__lte=date).aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"] or 0
        total = total - Decimal(self.virtual_balance)

        return Money(total, self.currency)

    def total_in_for_period(self, period="month", start_date=timezone.localdate()):
        period = calculate_period(periodicity=period, start_date=start_date, as_tuple=True)
        total = (
            self.transactions.filter(journal_entry__date__range=period)
            .filter(negative=False)
            .aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"]
        ) or 0

        return Money(total, self.currency)

    def total_out_for_period(self, period="month", start_date=timezone.localdate()):
        period = calculate_period(periodicity=period, start_date=start_date, as_tuple=True)
        total = (
            self.transactions.filter(journal_entry__date__range=period)
            .filter(negative=True)
            .aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"]
        ) or 0

        return Money(total, self.currency)

    def balance_for_period(self, period="month", start_date=timezone.localdate()):
        return self.total_in_for_period(period, start_date) + self.total_out_for_period(period, start_date)

    def journal_entries_for_period(self, period="month", start_date=timezone.localdate()):
        period = calculate_period(periodicity=period, start_date=start_date, as_tuple=True)

        return self.transactions.filter(journal_entry__date__range=period)