from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.functional import cached_property
from django.conf import settings

from djmoney.models.fields import MoneyField
from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money
from model_utils import FieldTracker

from .base import get_default_currency

import uuid


class Budget(models.Model):
    class Period(models.TextChoices):
        DAY = "day", "Daily"
        WEEK = "week", "Weekly"
        MONTH = "month", "Monthly"
        QUARTER = "quarter", "Quarterly"
        HALF_YEAR = "half_year", "Every 6 months"
        YEAR = "year", "Yearly"

    class AutoBudget(models.TextChoices):
        NO = "no", "No auto-budget"
        ADD = "add", "Add an amount each period"
        FIXED = "fixed", "Set a fixed amount each period"

    name = models.CharField(max_length=250)
    active = models.BooleanField("active?", default=True)
    amount = MoneyField(max_digits=15, decimal_places=2, default_currency=get_default_currency(), default=0)
    auto_budget = models.CharField("auto-budget", max_length=30, choices=AutoBudget.choices, default=AutoBudget.NO)
    auto_budget_period = models.CharField("auto-budget period", max_length=30, choices=Period.choices, default=Period.WEEK, blank=True, null=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    tracker = FieldTracker()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @cached_property
    def current_period(self):
        return self.get_period_for_date(date=timezone.now())

    @cached_property
    def used(self):
        return self.current_period.used

    @cached_property
    def available(self):
        return self.current_period.available

    def get_period_for_date(self, date):
        try:
            return self.periods.get(start_date__lte=date, end_date__gte=date)
        except BudgetPeriod.DoesNotExist:
            return None

    def get_periods(self):
        return self.periods.all()


class BudgetPeriod(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="periods")
    start_date = models.DateField()
    end_date = models.DateField()
    amount = MoneyField(max_digits=15, decimal_places=2)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["budget", "start_date"]
        get_latest_by = "start_date"

    def __str__(self):
        return "{i.budget.name}: {i.start_date} <> {i.end_date} ({i.amount})".format(i=self)

    @cached_property
    def used(self):
        from .transaction import TransactionJournalEntry

        currency = self.amount.currency
        total = Money(0, currency)

        for transaction in self.transactions.filter(
            transaction_type__in=[TransactionJournalEntry.TransactionType.WITHDRAWAL, TransactionJournalEntry.TransactionType.TRANSFER]
        ):
            total += convert_money(transaction.amount, currency)

        return total

    @cached_property
    def available(self):
        return self.amount - self.used
