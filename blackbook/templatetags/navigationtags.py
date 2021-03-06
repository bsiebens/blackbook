from django import template
from django.urls import resolve
from django.db.models import Count

# from ..models import Account

register = template.Library()


@register.simple_tag(takes_context=True)
def is_active(context, value):
    url = context.request.path
    url_name = resolve(url)

    if url_name.url_name.split("_")[0] == "accounts":
        if url_name.kwargs.get("account_type") == value:
            return "is-active"

    elif url_name.url_name.split("_")[0] == value:
        return "is-active"

    return None


# @register.inclusion_tag("blackbook/templatetags/account.html", takes_context=True)
# def accounts(context):
#     account_types = AccountType.objects.values("category").annotate(count=Count("accounts")).filter(count__gt=0).order_by("category")

#     return {"account_types": account_types, "request": context.get("request")}
