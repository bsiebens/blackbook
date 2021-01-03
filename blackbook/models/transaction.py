from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.functional import cached_property

from djmoney.models.fields import MoneyField
from djmoney.contrib.exchange.models import convert_money
from taggit.managers import TaggableManager
from model_utils import FieldTracker

from .base import get_default_currency
from .category import Category
from .budget import BudgetPeriod
from .account import Account

import uuid


class TransactionJournalEntry(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        START = "start", "Opening balance"
        RECONCILIATION = "reconciliation", "Reconciliation"
        TRANSFER = "transfer", "Transfer"
        WITHDRAWAL = "withdrawal", "Withdrawal"

    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=250)
    transaction_type = models.CharField(max_length=30, choices=TransactionType.choices, default=TransactionType.WITHDRAWAL)
    amount = MoneyField(max_digits=15, decimal_places=2, default_currency=get_default_currency(), default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions")
    budget = models.ForeignKey(BudgetPeriod, on_delete=models.SET_NULL, blank=True, null=True, related_name="transactions")
    tags = TaggableManager(blank=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)
    from_account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, related_name="from_transactions")
    to_account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, related_name="to_transactions")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    tracker = FieldTracker()

    class Meta:
        ordering = ["date", "created"]
        verbose_name_plural = "transaction journal entries"
        get_latest_by = "date"

    def __str__(self):
        return self.description

    def _create_transactions(self, to_account=None, from_account=None):
        if self.transaction_type in [self.TransactionType.START, self.TransactionType.DEPOSIT, self.TransactionType.RECONCILIATION]:
            if to_account is None:
                raise AttributeError("to_account should be specified for transaction type %s" % self.transaction_type)

            self.transactions.create(account=to_account, amount=self.amount, negative=False)

            if from_account is not None:
                self.transactions.create(account=from_account, amount=self.amount, negative=True)

        elif self.transaction_type == self.TransactionType.WITHDRAWAL:
            if from_account is None:
                raise AttributeError("from_account should be specified for transaction type %s" % self.transaction_type)

            self.transactions.create(account=from_account, amount=self.amount, negative=True)

            if to_account is not None:
                self.transactions.create(account=to_account, amount=self.amount, negative=False)

        else:
            if from_account is None or to_account is None:
                raise AttributeError("to_account and from_account should be specified for transaction type %s" % self.transaction_type)

            self.transactions.create(account=to_account, amount=self.amount, negative=False)
            self.transactions.create(account=from_account, amount=self.amount, negative=True)

    @classmethod
    def create_transaction(
        cls,
        amount,
        description,
        transaction_type,
        date=timezone.now(),
        category=None,
        budget=None,
        tags=None,
        from_account=None,
        to_account=None,
    ):
        journal_entry = cls.objects.create(
            date=date, description=description, transaction_type=transaction_type, amount=amount, category=category, budget=budget
        )
        journal_entry._create_transactions(to_account=to_account, from_account=from_account)

        if tags is not None:
            if isinstance(tags, str) and tags != "":
                tags = tags.replace(", ", ",").split(",")
            journal_entry.tags.set(*tags)

        return journal_entry

    def update(self, amount, description, transaction_type, date, budget=None, category=None, tags=None, from_account=None, to_account=None):
        self.amount = amount
        self.description = description
        self.transaction_type = transaction_type
        self.date = date
        self.budget = budget
        self.category = category

        if (
            self.tracker.has_changed("amount")
            or self.tracker.has_changed("transaction_type")
            or self.from_account != from_account
            or self.to_account != to_account
        ):
            self.transactions.all().delete()
            self._create_transactions(to_account=to_account, from_account=from_account)

        self.save()

        if tags is not None:
            if isinstance(tags, str) and tags != "":
                tags = tags.replace(", ", ",").split(",")
            self.tags.set(*tags)


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    journal_entry = models.ForeignKey(TransactionJournalEntry, on_delete=models.CASCADE, related_name="transactions")
    reconciled = models.BooleanField(default=False)
    amount = MoneyField(max_digits=15, decimal_places=2)
    negative = models.BooleanField(default=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Transaction {i.id}".format(i=self)

    def save(self, *args, **kwargs):
        self.amount = convert_money(self.journal_entry.amount, self.account.currency)

        if self.negative and self.amount.amount > 0:
            self.amount = self.amount * -1

        super(Transaction, self).save(*args, **kwargs)
