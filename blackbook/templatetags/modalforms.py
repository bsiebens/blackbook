from django import template
from django.urls import reverse

from ..forms import AccountForm
from ..models import Account
from ..utilities import set_message_and_redirect

register = template.Library()


@register.inclusion_tag("blackbook/templatetags/account_form.html")
def account_form():
    account = Account()
    account_form = AccountForm(None, instance=account)

    return {"account_form": account_form}