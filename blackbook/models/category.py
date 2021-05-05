from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property

from djmoney.money import Money
from decimal import Decimal

from .base import get_default_currency
from .transaction import Transaction

import uuid


class Category(models.Model):
    name = models.CharField(max_length=250)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @cached_property
    def total(self):
        return self.total_for_currrency(currency=get_default_currency())

    def total_for_currency(self, currency):
        return Money(
            Transaction.objects.filter(journal__category=self)
            .filter(amount_currency=currency)
            .aggregate(total=Coalesce(Sum("amount"), Decimal(0)))["total"],
            currency,
        )
