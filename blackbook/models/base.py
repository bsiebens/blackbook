from django.conf import settings

from ..utilities import get_currency


def get_default_value(key, default_value=None, user=None):
    try:
        profile = user.userprofile

        return getattr(profile, key.lower(), default_value)
    except:
        return getattr(settings, key.upper(), default_value)


def get_default_currency(user=None):
    return get_default_value("default_currency", "EUR", user)


def get_currency_choices(user=None):
    currencies = get_default_value("currencies", [])

    return [(currency, get_currency(currency=currency, user=user)) for currency in currencies]
