from django.utils import timezone
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django.template.defaultfilters import slugify

from dateutil.relativedelta import relativedelta, MO
from datetime import datetime, date
from babel.numbers import get_currency_name
from babel import Locale

import re


def set_message(request, message):
    message_flag = {"s": messages.SUCCESS, "f": messages.ERROR, "w": messages.WARNING, "i": messages.INFO}
    message_class = {"s": "success", "f": "danger", "w": "warning", "i": "info"}
    message_icon = {"s": "check", "f": "times", "w": "exclamation", "i": "info"}

    message_text = format_html(
        """
        <div class="notification is-{message_class}">
            <div class="level">
                <div class="level-left">
                    <div class="level-item">
                        <span class="icon">
                            <i class="fas fa-{message_icon}-circle"></i>
                        </span>
                    </div>
                    <div class="level-item">
                        {message_text}
                    </div>
                </div>
                <div class="level-right">
                    <div class="level-item">
                        <button type="button" class="button is-small is-white jb-notification-dismiss">
                            Dismiss
                        </button>
                    </div>
                </div>
            </div>
        </div>""".format(
            message_class=message_class[message[0:1]], message_icon=message_icon[message[0:1]], message_text=message[2:]
        )
    )
    messages.add_message(request, message_flag[message[0:1]], message_text, fail_silently=True)


def set_message_and_redirect(request, message, url):
    set_message(request, message)

    return redirect(url)


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


def unique_slugify(instance, value, slug_field_name="slug", queryset=None, slug_separator="-"):
    """
    Calculates and stores a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug, limiting its length if necessary.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create the queryset if one wasn't explicitly provided and exclude the
    # current instance from the queryset.
    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = "%s%s" % (slug_separator, next)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[: slug_len - len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = "%s%s" % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator="-"):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    separator = separator or ""
    if separator == "-" or not separator:
        re_sep = "-"
    else:
        re_sep = "(?:-|%s)" % re.escape(separator)
    # Remove multiple instances and if an alternate separator is provided,
    # replace the default '-' separator.
    if separator != re_sep:
        value = re.sub("%s+" % re_sep, separator, value)
    # Remove separator from the beginning and end of the slug.
    if separator:
        if separator != "-":
            re_sep = re.escape(separator)
        value = re.sub(r"^%s+|%s+$" % (re_sep, re_sep), "", value)
    return value