from django.db import models
from django.conf import settings

from djmoney.models.fields import CurrencyField

from .base import get_default_currency, get_currency_choices
from .budget import Budget


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    default_currency = CurrencyField(default=get_default_currency(), choices=get_currency_choices())
    default_period = models.CharField(max_length=30, choices=Budget.Period.choices, default=Budget.Period.MONTH)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)