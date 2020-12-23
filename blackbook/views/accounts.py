from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from djmoney.money import Money

from ..models import AccountType, Account, TransactionJournalEntry, Transaction
from ..utilities import set_message_and_redirect, calculate_period
from ..forms import AccountForm
from ..charts import AccountChart, TransactionChart


@login_required
def accounts(request, account_type, account_name=None):
    if account_name is not None:
        account = get_object_or_404(Account, slug=account_name)

        if account.user != request.user:
            return set_message_and_redirect(
                request, "f|You don't have access to this account.", reverse("blackbook:accounts", kwargs={"account_type": account_type})
            )

        period = request.user.userprofile.default_period
        account_chart = AccountChart(
            data=[account],
            start_date=calculate_period(periodicity=period)["start_date"],
            end_date=calculate_period(periodicity=period)["end_date"],
            user=request.user,
        ).generate_json()
        income_chart = TransactionChart(data=account.transactions, user=request.user, income=True).generate_json()
        expense_budget_chart = TransactionChart(data=account.transactions, user=request.user, expenses_budget=True).generate_json()
        expense_category_chart = TransactionChart(data=account.transactions, user=request.user, expenses_category=True).generate_json()
        income_chart_count = account.transactions.filter(negative=False).count()
        expense_budget_chart_count = account.transactions.filter(negative=True).exclude(journal_entry__budget=None).count()
        expense_category_chart_count = account.transactions.filter(negative=True).exclude(journal_entry__category=None).count()

        return render(
            request,
            "blackbook/accounts/detail.html",
            {
                "account": account,
                "account_chart": account_chart,
                "income_chart": income_chart,
                "expense_budget_chart": expense_budget_chart,
                "expense_category_chart": expense_category_chart,
                "income_chart_count": income_chart_count,
                "expense_budget_chart_count": expense_budget_chart_count,
                "expense_category_chart_count": expense_category_chart_count,
            },
        )

    else:
        account_type = get_object_or_404(AccountType, slug=account_type)
        accounts = Account.objects.filter(account_type=account_type).filter(user=request.user)

        return render(request, "blackbook/accounts/list.html", {"account_type": account_type, "accounts": accounts})


@login_required
def add_edit(request, account_name=None):
    account = Account()

    if account_name is not None:
        account = get_object_or_404(Account, slug=account_name)

        if account.user != request.user:
            return set_message_and_redirect(
                request, "f|You don't have access to this account.", reverse("blackbook:accounts", kwargs={"account_type": account_type})
            )

    account_form = AccountForm(request.POST or None, instance=account, initial={"starting_balance": account.starting_balance.amount})

    if request.POST and account_form.is_valid():
        account = account_form.save(commit=False)
        account.user = request.user
        account.save()

        if account_form.cleaned_data["starting_balance"] > 0:
            try:
                opening_balance_transaction = account.transactions.filter(
                    journal_entry__transaction_type=TransactionJournalEntry.TransactionType.START
                ).get(journal_entry__date=account.created.date())

                if opening_balance_transaction.amount != Money(account_form.cleaned_data["starting_balance"], account_form.cleaned_data["currency"]):
                    opening_balance_transaction.journal_entry.update(
                        amount=Money(account_form.cleaned_data["starting_balance"], account_form.cleaned_data["currency"]),
                        description="Starting balance",
                        transaction_type=TransactionJournalEntry.TransactionType.START,
                        date=account.created.date(),
                        to_account=account,
                    )

            except Transaction.DoesNotExist:
                TransactionJournalEntry.create_transaction(
                    amount=Money(account_form.cleaned_data["starting_balance"], account_form.cleaned_data["currency"]),
                    description="Starting balance",
                    transaction_type=TransactionJournalEntry.TransactionType.START,
                    user=request.user,
                    date=account.created.date(),
                    to_account=account,
                )

        return set_message_and_redirect(
            request,
            's|Account "{account.name}" was saved succesfully.'.format(account=account),
            reverse("blackbook:accounts", kwargs={"account_type": account.account_type.slug}),
        )

    return render(request, "blackbook/accounts/form.html", {"account_form": account_form, "account": account})


@login_required
def delete(request):
    if request.method == "POST":
        account = Account.objects.select_related("account_type").get(uuid=request.POST.get("account_uuid"))

        if account.user != request.user:
            return set_message_and_redirect(
                request,
                "f|You don't have access to delete this account.",
                reverse("blackbook:accounts", kwargs={"account_type", account.account_type.slug}),
            )

        account.delete()
        return set_message_and_redirect(
            request,
            's|Account "{account.name}" was succesfully deleted.'.format(account=account),
            reverse("blackbook:accounts", kwargs={"account_type": account.account_type.slug}),
        )

    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this.", reverse("blackbook:dashboard"))
