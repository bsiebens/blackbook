from django.db import models
from django.conf import settings

from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

from .base import get_default_currency

import uuid


class Category(models.Model):
    name = models.CharField(max_length=250)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def total(self):
        return self.total_in_currency(currency=get_default_currency())

    def total_in_currency(self, currency):
        total = Money(0, currency)

        for transaction in self.transactions.all():
            total += convert_money(transaction.amount, currency)

        return total