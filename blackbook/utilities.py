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


def calculate_period(periodicity, start_date=timezone.localtime(), as_tuple=False):
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


def display_period(periodicty, start_date=timezone.localdate()):
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


def validate_iban(iban):
    _country2length = dict(
        AL=28,
        AD=24,
        AT=20,
        AZ=28,
        BE=16,
        BH=22,
        BA=20,
        BR=29,
        BG=22,
        CR=21,
        HR=21,
        CY=28,
        CZ=24,
        DK=18,
        DO=28,
        EE=20,
        FO=18,
        FI=18,
        FR=27,
        GE=22,
        DE=22,
        GI=23,
        GR=27,
        GL=18,
        GT=28,
        HU=28,
        IS=26,
        IE=22,
        IL=23,
        IT=27,
        KZ=20,
        KW=30,
        LV=21,
        LB=28,
        LI=21,
        LT=20,
        LU=20,
        MK=19,
        MT=31,
        MR=27,
        MU=30,
        MC=27,
        MD=24,
        ME=22,
        NL=18,
        NO=15,
        PK=24,
        PS=29,
        PL=28,
        PT=25,
        RO=24,
        SM=27,
        SA=24,
        RS=22,
        SK=24,
        SI=19,
        ES=24,
        SE=24,
        CH=21,
        TN=24,
        TR=26,
        AE=23,
        GB=22,
        VG=24,
    )

    # Check if empty
    if iban == "":
        return True

    # Ensure upper alphanumeric input.
    iban = iban.replace(" ", "").replace("\t", "")
    if not re.match(r"^[\dA-Z]+$", iban):
        return False
    # Validate country code against expected length.
    if len(iban) != _country2length[iban[:2]]:
        return False
    # Shift and convert.
    iban = iban[4:] + iban[:4]
    digits = int("".join(str(int(ch, 36)) for ch in iban))  # BASE 36: 0..9,A..Z -> 0..35
    return digits % 97 == 1


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

        from .models import Account

        if instance.__class__.__base__ == Account:
            queryset = instance.__class__.__base__._default_manager.all()

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