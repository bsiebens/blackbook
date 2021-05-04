from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum, Q
from django.utils import timezone

from djmoney.money import Money

from ..models import Transaction, TransactionJournal, Account, get_default_currency
from ..utilities import set_message_and_redirect, calculate_period, set_message
from ..charts import TransactionChart
from ..forms import TransactionForm

import datetime
import re

ACCOUNT_REGEX = re.compile(r"(.*)\s-\s(.*)")


@login_required
def add_edit(request, transaction_uuid=None):
    initial_data = {}
    transaction_journal = TransactionJournal()

    initial_amount = Money(0, get_default_currency(user=request.user))
    initial_data["amount"] = initial_amount

    if transaction_uuid is not None:
        transaction_journal = TransactionJournal.objects.prefetch_related("transactions", "transactions__account").get(uuid=transaction_uuid)

        initial_data = {
            "amount": initial_amount,
            "short_description": transaction_journal.short_description,
            "description": transaction_journal.description,
            "type": transaction_journal.type,
            "date": transaction_journal.date,
            "source_account": None,
            "destination_account": None,
        }

        if transaction_journal.type == TransactionJournal.TransactionType.WITHDRAWAL:
            initial_data["amount"] = abs(transaction_journal.transactions.get(amount__lte=0).amount)
        elif transaction_journal.type == TransactionJournal.TransactionType.DEPOSIT:
            initial_data["amount"] = abs(transaction_journal.transactions.get(amount__gte=0).amount)
        else:
            initial_data["amount"] = abs(transaction_journal.transactions.first().amount)

        if len(transaction_journal.source_accounts) > 0:
            initial_data["source_account"] = "{type} - {name}".format(
                type=transaction_journal.source_accounts[0]["type"], name=transaction_journal.source_accounts[0]["account"]
            )

        if len(transaction_journal.destination_accounts) > 0:
            initial_data["destination_account"] = "{type} - {name}".format(
                type=transaction_journal.destination_accounts[0]["type"], name=transaction_journal.destination_accounts[0]["account"]
            )

    transaction_form = TransactionForm(request.user, request.POST or None, initial=initial_data)

    if request.POST and transaction_form.is_valid():
        return_url = reverse("blackbook:dashboard")

        if transaction_form.cleaned_data["add_new"]:
            return_url = reverse("blackbook:transactions_add")

        transaction = {
            "short_description": transaction_form.cleaned_data["short_description"],
            "description": transaction_form.cleaned_data["description"],
            "date": transaction_form.cleaned_data["date"],
            "type": transaction_form.cleaned_data["type"],
            "transactions": [],
        }

        for account_type_key in ["source_account", "destination_account"]:
            if transaction_form.cleaned_data[account_type_key] != "":
                account_name = transaction_form.cleaned_data[account_type_key]

                account_type = Account.AccountType.REVENUE_ACCOUNT
                if account_type_key == "destination_account":
                    account_type = Account.AccountType.EXPENSE_ACCOUNT

                if ACCOUNT_REGEX.match(transaction_form.cleaned_data[account_type_key]) is not None:
                    account_name = ACCOUNT_REGEX.match(transaction_form.cleaned_data[account_type_key])[2]

                    for type in Account.AccountType:
                        if type.label == ACCOUNT_REGEX.match(transaction_form.cleaned_data[account_type_key])[1]:
                            account_type = type

                account, account_created = Account.objects.get_or_create(
                    name=account_name, type=account_type, defaults={"type": account_type, "net_worth": False, "dashboard": False}
                )

                if account_created:
                    set_message(request, 's|Account "{account.name}" saved succesfully.'.format(account=account))

                amount = transaction_form.cleaned_data["amount"]
                if account_type_key == "source_account":
                    amount *= -1

                transaction["transactions"].append({"account": account, "amount": amount})

        if transaction_uuid is None:
            transaction_journal = TransactionJournal.create(transactions=transaction)
        else:
            transaction_journal.update(transactions=transaction)

        if transaction_form.cleaned_data["display"]:
            return_url = reverse("blackbook:transactions_edit", kwargs={"transaction_uuid": transaction_journal.uuid})

        return set_message_and_redirect(
            request,
            's|Transaction "{short_description}" saved succesfully.'.format(short_description=transaction_form.cleaned_data["short_description"]),
            return_url,
        )

    return render(
        request,
        "blackbook/transactions/form.html",
        {"transaction_form": transaction_form, "transaction_journal": transaction_journal, "amount": initial_data["amount"]},
    )
