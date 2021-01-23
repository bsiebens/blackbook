from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.functional import cached_property

from localflavor.generic.models import IBANField
from djmoney.money import Money
from djmoney.models.fields import CurrencyField

from .base import get_default_currency, get_currency_choices
from ..utilities import calculate_period, unique_slugify

import uuid


class Account(models.Model):
    class AccountType(models.TextChoices):
        ASSET_ACCOUNT = "assetaccount", "asset account"
        REVENUE_ACCOUNT = "revenueaccount", "revenue account"
        EXPENSE_ACCOUNT = "expenseaccount", "expense account"
        LIABILITIES_ACCOUNT = "liabilitiesaccount", "liabilities"
        CASH_ACCOUNT = "cashaccount", "cash account"

    name = models.CharField(max_length=250)
    slug = models.SlugField(editable=False, db_index=True, unique=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)
    active = models.BooleanField("active?", default=True)
    net_worth = models.BooleanField("include in net worth?", default=True, help_text="Include this account when calculating total net worth?")
    dashboard = models.BooleanField("show on dashboard?", default=True, help_text="Show this transaction on the dashboard?")
    currency = CurrencyField(default=get_default_currency(), choices=get_currency_choices())
    virtual_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.0,
        help_text="Enter a number here to have BlackBook treat this as the new zero point for this account. Default should always be 0.0",
    )
    type = models.CharField(max_length=50, choices=AccountType.choices)
    icon = models.CharField(max_length=50)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        unique_slugify(self, self.name)
        super(Account, self).save(*args, **kwargs)

    @property
    def account(self):
        return getattr(self, self.type)

    @cached_property
    def starting_balance(self):
        try:
            opening_balance = (
                self.transactions.select_related("transaction")
                .filter(transaction__type=Transaction.TransactionType.START)
                .get(transaction__date=self.created)
            )
            return Money(opening_balance, self.currency) - Money(self.virtual_balance, self.currency)

        except:
            return Money(self.virtual_balance, self.currency) * -1

    @cached_property
    def balance(self):
        return self.balance_until_date()

    def balance_until_date(self, date=timezone.localdate()):
        total = Money(self.transactions.filter(transaction__date__lte=date).aggregate(total=Coalesce(Sum("amount"), 0))["total"], self.currency)

        return total - Money(self.virtual_balance, self.currency)


class AssetAccount(Account):
    iban = IBANField("IBAN", null=True, blank=True)

    def save(self, *args, **kwargs):
        self.type = Account.AccountType.ASSET_ACCOUNT
        self.icon = "fa-landmark"

        super().save(*args, **kwargs)


class RevenueAccount(Account):
    iban = IBANField("IBAN", null=True, blank=True)

    def save(self, *args, **kwargs):
        self.type = Account.AccountType.REVENUE_ACCOUNT
        self.icon = "fa-donate"

        super().save(*args, **kwargs)


class ExpenseAccount(Account):
    iban = IBANField("IBAN", null=True, blank=True)

    def save(self, *args, **kwargs):
        self.type = Account.AccountType.EXPENSE_ACCOUNT
        self.icon = "fa-file-invoice-dollar"

        super().save(*args, **kwargs)


class LiabilitiesAccount(Account):
    account_number = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.type = Account.AccountType.LIABILITIES_ACCOUNT
        self.icon = "fa-home"

        super().save(*args, **kwargs)


class CashAccount(Account):
    def save(self, *args, **kwargs):
        self.type = Account.AccountType.CASH_ACCOUNT
        self.icon = "fa-coins"

        super().save(*args, **kwargs)