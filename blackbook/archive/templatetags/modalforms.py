from django import template
from django.urls import reverse

from ..forms import AccountForm, TransactionForm
from ..models import Account
from ..utilities import set_message_and_redirect

register = template.Library()


@register.inclusion_tag("blackbook/templatetags/account_form.html")
def account_form():
    account = Account()
    account_form = AccountForm(None, instance=account)

    return {"account_form": account_form}


@register.inclusion_tag("blackbook/templatetags/transaction_form.html", takes_context=True)
def transaction_form(context):
    user = context.request.user
    transaction_form = TransactionForm(user, None)

    return {"transaction_form": transaction_form}