from django.db import models
from django.utils import timezone

from djmoney.models.fields import MoneyField

from .base import get_default_currency
from .account import Account

import uuid


class TransactionJournal(models.Model):
    date = models.DateField(default=timezone.localdate)
    short_description = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "created"]
        get_latest_by = "date"

    def __str__(self):
        return self.short_description


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        START = "start", "Opening balance"
        RECONCILIATION = "reconciliation", "Reconciliation"
        TRANSFER = "transfer", "Transfer"
        WITHDRAWAL = "withdrawal", "Withdrawal"

    type = models.CharField(max_length=50, choices=TransactionType.choices, default=TransactionType.WITHDRAWAL)
    source_account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True, related_name="source_account")
    destination_account = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True, related_name="destination_account")
    amount = MoneyField("amount", max_digits=15, decimal_places=2, default_currency=get_default_currency(), default=0)
    foreign_amount = MoneyField(
        "foreign amount", max_digits=15, decimal_places=2, default_currency=get_default_currency(), default=0, blank=True, null=True
    )
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)
    journal = models.ForeignKey(TransactionJournal, on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.journal.short_description

    def save(self, *args, **kwargs):
        self.type = self._verify_transaction_type(type=self.type)

        super(Transaction, self).save(*args, **kwargs)

    def _verify_transaction_type(self, type):
        if type in [self.TransactionType.START, self.TransactionType.RECONCILIATION]:
            return type

        owned_accounts = [Account.AccountType.ASSET_ACCOUNT, Account.AccountType.LIABILITIES_ACCOUNT]

        if self.source_account is not None:
            if self.source_account.type in owned_accounts:
                if self.destination_account is not None and self.destination_account in owned_accounts:
                    return self.TransactionType.TRANSFER

                return self.TransactionType.WITHDRAWAL

            else:
                if self.destination_account is not None and self.destination_account in owned_accounts:
                    return self.TransactionType.DEPOSIT

                return self.TransactionType.WITHDRAWAL

        return self.TransactionType.DEPOSIT