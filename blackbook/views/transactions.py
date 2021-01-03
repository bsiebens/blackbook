from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum, Q
from django.utils import timezone

from ..models import TransactionJournalEntry, Transaction, Account, Category, Budget, AccountType
from ..utilities import set_message_and_redirect, calculate_period, set_message
from ..forms import TransactionForm, TransactionFilterForm
from ..charts import TransactionChart

import datetime
import re

ACCOUNT_REGEX = re.compile(r".*\s-\s(.*)")


@login_required
def transactions(request):
    transactions = Transaction.objects.all()
    journal_entries = TransactionJournalEntry.objects.all()
    date_range = calculate_period(periodicity=request.user.userprofile.default_period, start_date=timezone.localdate(), as_tuple=True)

    filter_form = TransactionFilterForm(request.GET or None, initial={"start_date": date_range[0], "end_date": date_range[1]})
    if filter_form.is_valid():
        date_range = (filter_form.cleaned_data["start_date"], filter_form.cleaned_data["end_date"])

        if filter_form.cleaned_data["description"] != "":
            transactions = transactions.filter(journal_entry__description__icontains=filter_form.cleaned_data["description"])
            journal_entries = journal_entries.filter(description__icontains=filter_form.cleaned_data["description"])

        if filter_form.cleaned_data["account"] != "":
            account = Account.objects.get(name=filter_form.cleaned_data["account"])
            transactions = transactions.filter(account=account)
            journal_entries = journal_entries.filter(Q(to_account=account) | Q(from_account=account))

        if filter_form.cleaned_data["category"] != "":
            category = Category.objects.get(name=filter_form.cleaned_data["category"])
            transactions = transactions.filter(journal_entry__category=category)
            journal_entries = journal_entries.filter(category=category)

        if filter_form.cleaned_data["budget"] != "":
            budget = Budget.objects.get(name=filter_form.cleaned_data["budget"])
            transactions = transactions.filter(journal_entry__budget__budget=budget)
            journal_entries = journal_entries.filter(budget__budget=budget)

    transactions = (
        transactions.filter(journal_entry__date__range=date_range)
        .select_related(
            "journal_entry",
            "account",
            "journal_entry__budget__budget",
            "journal_entry__category",
            "journal_entry__from_account__account_type",
        )
        .values(
            "amount_currency",
            "negative",
            "account__name",
            "account__virtual_balance",
            "journal_entry__transaction_type",
            "journal_entry__budget__budget__name",
            "journal_entry__category__name",
            "journal_entry__from_account__name",
            "journal_entry__from_account__account_type__category",
        )
        .annotate(total=Sum("amount"))
    )
    journal_entries = (
        journal_entries.filter(date__range=date_range)
        .select_related("budget__budget", "category", "to_account", "from_account")
        .prefetch_related("transactions")
        .order_by("-date", "-created")
    )

    charts = {
        "income_chart": TransactionChart(data=transactions, user=request.user, income=True).generate_json(),
        "expense_budget_chart": TransactionChart(data=transactions, user=request.user, expenses_budget=True).generate_json(),
        "expense_category_chart": TransactionChart(data=transactions, user=request.user, expenses_category=True).generate_json(),
        "income_chart_count": len([item for item in transactions if not item["negative"]]),
        "expense_budget_chart_count": len(
            [item for item in transactions if item["negative"] and item["journal_entry__budget__budget__name"] is not None]
        ),
        "expense_category_chart_count": len(
            [item for item in transactions if item["negative"] and item["journal_entry__category__name"] is not None]
        ),
    }

    return render(
        request,
        "blackbook/transactions/list.html",
        {"filter_form": filter_form, "period": date_range, "charts": charts, "journal_entries": journal_entries},
    )


@login_required
def add_edit(request, transaction_uuid=None):
    initial_data = {}
    transaction = Transaction()

    if transaction_uuid is not None:
        transaction = Transaction.objects.select_related(
            "journal_entry",
            "journal_entry__budget__budget",
            "journal_entry__from_account",
            "journal_entry__to_account",
            "journal_entry__category",
            "account__account_type",
        ).get(uuid=transaction_uuid)

        initial_data = {
            "amount": transaction.journal_entry.amount,
            "description": transaction.journal_entry.description,
            "transaction_type": transaction.journal_entry.transaction_type,
            "date": transaction.journal_entry.date,
            "category": transaction.journal_entry.category.name if transaction.journal_entry.category is not None else None,
            "budget": transaction.journal_entry.budget.budget.name if transaction.journal_entry.budget is not None else None,
            "tags": ", ".join([tag.name for tag in transaction.journal_entry.tags.all()]),
            "from_account": "{transaction.journal_entry.from_account.account_type} - {transaction.journal_entry.from_account.name}".format(
                transaction=transaction
            )
            if transaction.journal_entry.from_account is not None
            else None,
            "to_account": "{transaction.journal_entry.to_account.account_type} - {transaction.journal_entry.to_account.name}".format(
                transaction=transaction
            )
            if transaction.journal_entry.to_account is not None
            else None,
        }

    transaction_form = TransactionForm(request.user, request.POST or None, initial=initial_data)

    if request.POST and transaction_form.is_valid():
        return_url = None

        if transaction_form.cleaned_data["add_new"]:
            return_url = reverse("blackbook:transactions_add")

        category = category_created = budget = budget_created = from_account = from_account_created = to_account = to_account_created = None

        if transaction_form.cleaned_data["category"] != "":
            category, category_created = Category.objects.get_or_create(name=transaction_form.cleaned_data["category"])

        if transaction_form.cleaned_data["budget"] != "":
            budget, budget_created = Budget.objects.get_or_create(name=transaction_form.cleaned_data["budget"])

        if transaction_form.cleaned_data["from_account"] != "":
            account_type = AccountType.objects.get(name="Revenue account")
            account_name = (
                ACCOUNT_REGEX.match(transaction_form.cleaned_data["from_account"])[1]
                if ACCOUNT_REGEX.match(transaction_form.cleaned_data["from_account"]) is not None
                else transaction_form.cleaned_data["from_account"]
            )
            from_account, from_account_created = Account.objects.get_or_create(
                name=account_name,
                defaults={
                    "account_type": account_type,
                    "include_in_net_worth": False,
                    "include_on_dashboard": False,
                },
            )

        if transaction_form.cleaned_data["to_account"] != "":
            account_type = AccountType.objects.get(name="Expense account")
            account_name = (
                ACCOUNT_REGEX.match(transaction_form.cleaned_data["to_account"])[1]
                if ACCOUNT_REGEX.match(transaction_form.cleaned_data["to_account"]) is not None
                else transaction_form.cleaned_data["to_account"]
            )
            to_account, to_account_created = Account.objects.get_or_create(
                name=account_name,
                defaults={
                    "account_type": account_type,
                    "include_in_net_worth": False,
                    "include_on_dashboard": False,
                },
            )

        if category_created:
            set_message(request, 's|Category "{category.name}" saved succesfully.'.format(category=category))

        if budget_created:
            set_message(request, 's|Budget "{budget.name}" saved succesfully.'.format(budget=budget))

        if from_account_created:
            set_message(request, 's|Account "{account.name}" saved succesfully.'.format(account=from_account))

        if to_account_created:
            set_message(request, 's|Account "{account.name}" saved succesfully.'.format(account=to_account))

        if transaction_uuid is not None:
            transaction.journal_entry.update(
                amount=transaction_form.cleaned_data["amount"],
                description=transaction_form.cleaned_data["description"],
                transaction_type=transaction_form.cleaned_data["transaction_type"],
                date=transaction_form.cleaned_data["date"],
                category=category,
                budget=budget.get_period_for_date(transaction_form.cleaned_data["date"]) if transaction_form.cleaned_data["budget"] != "" else None,
                tags=transaction_form.cleaned_data["tags"],
                from_account=from_account,
                to_account=to_account,
            )

            if transaction_form.cleaned_data["display"]:
                return_url = reverse("blackbook:journal_entries_edit", kwargs={"journal_entry_uuid": transaction.journal_entry.uuid})

            if return_url is None:
                return_url = reverse(
                    "blackbook:accounts", kwargs={"account_type": transaction.account.account_type.category, "account_name": transaction.account.slug}
                )

            return set_message_and_redirect(
                request,
                's|Transaction "{description}" saved succesfully.'.format(description=transaction_form.cleaned_data["description"]),
                return_url,
            )

        else:
            transaction = TransactionJournalEntry.create_transaction(
                amount=transaction_form.cleaned_data["amount"],
                description=transaction_form.cleaned_data["description"],
                transaction_type=transaction_form.cleaned_data["transaction_type"],
                # user=request.user,
                date=transaction_form.cleaned_data["date"],
                category=category,
                budget=budget.get_period_for_date(transaction_form.cleaned_data["date"]) if transaction_form.cleaned_data["budget"] != "" else None,
                tags=transaction_form.cleaned_data["tags"],
                from_account=from_account,
                to_account=to_account,
            )

            if transaction_form.cleaned_data["display"]:
                return_url = reverse("blackbook:journal_entries_edit", kwargs={"journal_entry_uuid": transaction.uuid})

            if return_url is None:
                account = (
                    transaction.from_account
                    if transaction.transaction_type == TransactionJournalEntry.TransactionType.WITHDRAWAL
                    or transaction.transaction_type == TransactionJournalEntry.TransactionType.TRANSFER
                    else transaction.to_account
                )

                return_url = reverse("blackbook:accounts", kwargs={"account_type": account.account_type.category, "account_name": account.slug})

            return set_message_and_redirect(
                request,
                's|Transaction "{description}" saved succesfully.'.format(description=transaction_form.cleaned_data["description"]),
                return_url,
            )

    return render(request, "blackbook/transactions/form.html", {"transaction_form": transaction_form, "transaction": transaction})


@login_required
def delete(request):
    if request.method == "POST":
        transaction = (
            Transaction.objects.select_related("journal_entry").select_related("account__account_type").get(uuid=request.POST.get("transaction_uuid"))
        )

        transaction.journal_entry.delete()
        return set_message_and_redirect(
            request,
            's|Transaction "{transaction.journal_entry.description}" was succesfully deleted.'.format(transaction=transaction),
            reverse(
                "blackbook:accounts", kwargs={"account_type": transaction.account.account_type.category, "account_name": transaction.account.slug}
            ),
        )

    else:
        return set_message_and_redirect(
            request,
            "w|You are not allowed to access this page like this.",
            reverse(
                "blackbook:accounts", kwargs={"account_type": transaction.account.account_type.category, "account_name": transaction.account.slug}
            ),
        )


@login_required
def journal_entry_edit(request, journal_entry_uuid):
    journal_entry = get_object_or_404(TransactionJournalEntry, uuid=journal_entry_uuid)

    return redirect(reverse("blackbook:transactions_edit", kwargs={"transaction_uuid": journal_entry.transactions.all().first().uuid}))


@login_required
def journal_entry_delete(request):
    if request.method == "POST":
        journal_entry = TransactionJournalEntry.objects.get(uuid=request.POST.get("journal_entry_uuid"))

        journal_entry.delete()
        return set_message_and_redirect(
            request,
            's|Transaction "{journal_entry.description}" was succesfully deleted.'.format(journal_entry=journal_entry),
            reverse("blackbook:transactions"),
        )

    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this.", reverse("blackbook:transactions"))
