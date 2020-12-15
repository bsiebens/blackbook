from django.db import models
from django.conf import settings

from babel.numbers import get_currency_name
from babel import Locale


def get_default_value(key, default_value=None, user=None):
    if user is None:
        return getattr(settings, key.upper(), default_value)

    try:
        profile = user.userprofile
        return getattr(profile, key.lower(), default_value)
    except:
        return getattr(settings, key.upper(), default_value)


def get_default_currency(user=None):
    return get_default_value("default_currency", "EUR", user)


def get_currency_choices(user=None):
    currencies = get_default_value("currencies", [])
    locale = get_default_value("language_code", "en-us", user).split("-")
    locale = Locale(locale[0], locale[1])

    return [(currency, get_currency_name(currency, locale=locale)) for currency in currencies]