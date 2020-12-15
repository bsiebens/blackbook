from django.db import models
from django.conf import settings

from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money

from .base import get_default_currency


class Category(models.Model):
    name = models.CharField(max_length=250)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]
        permissions = [
            ("category_owner", "Category owner"),
            ("category_viewer", "Category viewer"),
        ]

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