from django import template
from django.urls import resolve
from django.db.models import Count

from ..models import AccountType

register = template.Library()


@register.simple_tag(takes_context=True)
def is_active(context, value):
    url = context.request.path
    url_name = resolve(url)

    if url_name.url_name == "accounts":
        if url_name.kwargs.get("account_type") == value:
            return "is-active"

    elif url_name.url_name == value:
        return "is-active"

    return None
    

@register.inclusion_tag("blackbook/templatetags/account.html", takes_context=True)
def accounts(context):
    account_types = AccountType.objects.annotate(count=Count("accounts")).filter(count__gt=0)
    
    return {"account_types": account_types, "request": context.get("request")}
