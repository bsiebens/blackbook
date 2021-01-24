from django.db import models
from django.utils import timezone

from djmoney.models.fields import MoneyField

from .base import get_default_currency
from .account import Account

import uuid


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        START = "start", "Opening balance"
        RECONCILIATION = "reconciliation", "Reconciliation"
        TRANSFER = "transfer", "Transfer"
        WITHDRAWAL = "withdrawal", "Withdrawal"

    date = models.DateField(default=timezone.localdate)
    short_description = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=TransactionType.choices, default=TransactionType.WITHDRAWAL)
    amount_source_currency = MoneyField("source amount", max_digits=15, decimal_places=2, default_currency=get_default_currency(), default=0)
    amount_destination_currency = MoneyField(
        "destination amount", max_digits=15, decimal_places=2, default_currency=get_default_currency(), default=0
    )
    source_account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True, related_name="source_account")
    destination_account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True, related_name="destination_account")
    linked_transactions = models.ManyToManyField("self", blank=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "created"]
        get_latest_by = "date"

    def __str__(self):
        return self.short_description