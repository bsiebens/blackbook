from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from localflavor.generic.models import IBANField
from djmoney.models.fields import CurrencyField
from djmoney.money import Money

from .base import get_default_currency, get_default_value, get_currency_choices
from ..utilities import calculate_period


class AccountType(models.Model):
    name = models.CharField(max_length=250)
    icon = models.CharField(max_length=250, default="fa-coins")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Account(models.Model):
    name = models.CharField(max_length=250)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, related_name="accounts")
    active = models.BooleanField("active?", default=True)
    include_in_net_worth = models.BooleanField(
        "include in net worth?", default=True, help_text="Include this account when calculating total net worth?"
    )
    iban = IBANField("IBAN", null=True, blank=True)
    currency = CurrencyField(default=get_default_currency(), choices=get_currency_choices())
    virtual_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.0,
        help_text="Enter a number here to have BlackBook treat this as the new zero point for this account. Leave at 0.0 to disable.",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("account_owner", "Account owner"),
            ("account_viewer", "Account viewer"),
        ]

    def __str__(self):
        return self.name

    @property
    def balance(self):
        return self.balance_until_date()

    def balance_until_date(self, date=timezone.now()):
        total = self.transactions.filter(journal_entry__date__lte=date).aggregate(total=Coalesce(Sum("amount"), 0))["total"]

        return Money(total, self.currency)

    def total_in_for_period(self, period="month", start_date=timezone.now()):
        period = calculate_period(periodicity=period, start_date=start_date, as_tuple=True)
        total = (
            self.transactions.filter(journal_entry__date__range=period).filter(negative=False).aggregate(total=Coalesce(Sum("amount"), 0))["total"]
        )

        return Money(total, self.currency)

    def total_out_for_period(self, period="month", start_date=timezone.now()):
        period = calculate_period(periodicity=period, start_date=start_date, as_tuple=True)
        total = self.transactions.filter(journal_entry__date__range=period).filter(negative=True).aggregate(total=Coalesce(Sum("amount"), 0))["total"]

        return Money(total, self.currency)

    def balance_for_period(self, period="month", start_date=timezone.now()):
        return self.total_in_for_period(period, start_date) + self.total_out_for_period(period, start_date)

    def journal_entries_for_period(self, period="month", start_date=timezone.now()):
        period = calculate_period(periodicity=period, start_date=start_date, as_tuple=True)

        return self.transactions.filter(journal_entry__date__range=period)