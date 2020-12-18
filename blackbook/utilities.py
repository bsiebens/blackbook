from django.utils import timezone

from dateutil.relativedelta import relativedelta, MO
from datetime import datetime, date
from babel.numbers import get_currency_name
from babel import Locale


def calculate_period(periodicity, start_date=timezone.now(), as_tuple=False):
    if type(start_date) == datetime:
        start_date = start_date.date()

    if type(start_date) != date:
        raise AttributeError("start date should be a date or datetime object")

    periodicity_to_relativedate_transformer = {
        "day": {
            "start": relativedelta(days=0),
            "end": relativedelta(days=0),
        },
        "week": {
            "start": relativedelta(weekday=MO(-1)),
            "end": relativedelta(days=6),
        },
        "month": {
            "start": relativedelta(day=1),
            "end": relativedelta(months=1, days=-1),
        },
        "quarter": {
            "start": relativedelta(day=1, month=(3 * ((start_date.month - 1) // 3) + 1)),
            "end": relativedelta(months=3, days=-1),
        },
        "half_year": {
            "start": relativedelta(day=1, month=(6 * ((start_date.month - 1) // 6) + 1)),
            "end": relativedelta(months=6, days=-1),
        },
        "year": {
            "start": relativedelta(day=1, month=1),
            "end": relativedelta(years=1, days=-1),
        },
    }

    start_date += periodicity_to_relativedate_transformer[periodicity]["start"]
    end_date = start_date + periodicity_to_relativedate_transformer[periodicity]["end"]

    if as_tuple:
        return (start_date, end_date)

    return {"start_date": start_date, "end_date": end_date}


def display_period(periodicty, start_date=timezone.now().date()):
    if periodicty == "day":
        return start_date.strftime("%d %b %Y")
    elif periodicty == "week":
        return "Week of {date}".format(date=(start_date + relativedelta(weekday=MO(-1))).strftime("%d %b %Y"))
    elif periodicty == "month":
        return start_date.strftime("%b %Y")
    elif periodicty == "quarter":
        if start_date.month <= 3:
            return "Quarter 1 {year}".format(year=start_date.year)
        elif start_date.month <= 6:
            return "Quarter 2 {year}".format(year=start_date.year)
        elif start_date.month <= 9:
            return "Quarter 3 {year}".format(year=start_date.year)
        else:
            return "Quarter 4 {year}".format(year=start_date.year)
    elif periodicty == "half_year":
        if start_date.month <= 6:
            return "First half {year}".format(year=start_date.year)
        else:
            return "Second half {year}".format(year=start_date.year)
    else:
        return start_date.year


def format_iban(value, grouping=4):
    if value is None:
        return None

    value = value.upper().replace(" ", "").replace("-", "")

    return " ".join(value[i : i + grouping] for i in range(0, len(value), grouping))


def get_currency(currency, user=None):
    from .models import get_default_value

    locale = get_default_value("language_code", "en-us", user).split("-")
    locale = Locale(locale[0], locale[1].upper())

    return get_currency_name(currency, locale=locale)