from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum, Prefetch
from django.db.models.functions import Coalesce
from django.utils import timezone

from djmoney.money import Money

from ..models import AccountType, Account, TransactionJournalEntry, Transaction
from ..utilities import set_message_and_redirect, calculate_period
from ..forms import AccountForm
from ..charts import AccountChart, TransactionChart


@login_required
def accounts(request, account_type, account_name=None):
    if account_name is not None:
        period = calculate_period(periodicity=request.user.userprofile.default_period, start_date=timezone.localdate())

        account = get_object_or_404(
            Account.objects.select_related("account_type")
            .prefetch_related(
                Prefetch(
                    "transactions",
                    Transaction.objects.filter(journal_entry__date__range=(period["start_date"], period["end_date"])),
                ),
            )
            .prefetch_related("transactions__journal_entry")
            .prefetch_related("transactions__journal_entry__tags")
            .prefetch_related("transactions__journal_entry__budget__budget")
            .prefetch_related("transactions__journal_entry__category")
            .prefetch_related("transactions__journal_entry__from_account__account_type")
            .prefetch_related("transactions__journal_entry__to_account__account_type")
            .annotate(total=Coalesce(Sum("transactions__amount"), 0))
            .order_by("transactions__journal_entry__date", "transactions__journal_entry__created"),
            slug=account_name,
        )

        account.total = Money(account.total - account.virtual_balance, account.currency)

        # if account.user != request.user:
        #     return set_message_and_redirect(
        #         request, "f|You don't have access to this account.", reverse("blackbook:accounts", kwargs={"account_type": account_type})
        #     )

        transactions = (
            Transaction.objects.filter(account=account)
            .select_related("journal_entry", "account", "journal_entry__budget__budget", "journal_entry__category", "journal_entry__from_account")
            .filter(journal_entry__date__range=(period["start_date"], period["end_date"]))
            .values(
                "amount_currency",
                "negative",
                "account__name",
                "account__virtual_balance",
                "journal_entry",
                "journal_entry__date",
                "journal_entry__transaction_type",
                "journal_entry__budget__budget__name",
                "journal_entry__category__name",
                "journal_entry__from_account__name",
            )
            .annotate(total=Sum("amount"))
            .order_by("-journal_entry__date", "-journal_entry__created")
        )

        in_for_period = Money(sum([transaction["total"] for transaction in transactions if not transaction["negative"]]), account.currency)
        out_for_period = Money(sum([transaction["total"] for transaction in transactions if transaction["negative"]]), account.currency)
        balance_for_period = in_for_period + out_for_period

        charts = {
            "account_chart": AccountChart(
                data=transactions,
                start_date=period["start_date"],
                end_date=period["end_date"],
                user=request.user,
            ).generate_json(),
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
            "blackbook/accounts/detail.html",
            {
                "account": account,
                "charts": charts,
                "in_for_period": in_for_period,
                "out_for_period": out_for_period,
                "balance_for_period": balance_for_period,
                "period": period,
            },
        )

    else:
        account_type = get_object_or_404(AccountType, slug=account_type)
        accounts = Account.objects.filter(account_type=account_type).annotate(total=Coalesce(Sum("transactions__amount"), 0))

        for account in accounts:
            account.total -= account.virtual_balance

        return render(request, "blackbook/accounts/list.html", {"account_type": account_type, "accounts": accounts})


@login_required
def add_edit(request, account_name=None):
    account = Account()

    if account_name is not None:
        account = get_object_or_404(Account, slug=account_name)

        # if account.user != request.user:
        #     return set_message_and_redirect(
        #         request, "f|You don't have access to this account.", reverse("blackbook:accounts", kwargs={"account_type": account_type})
        #     )

    account_form = AccountForm(request.POST or None, instance=account, initial={"starting_balance": account.starting_balance.amount})

    if request.POST and account_form.is_valid():
        account = account_form.save(commit=False)
        # account.user = request.user
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
                    # user=request.user,
                    date=account.created.date(),
                    to_account=account,
                )

        return set_message_and_redirect(
            request,
            's|Account "{account.name}" was saved succesfully.'.format(account=account),
            reverse("blackbook:accounts", kwargs={"account_type": account.account_type.slug, "account_name": account.slug}),
        )

    return render(request, "blackbook/accounts/form.html", {"account_form": account_form, "account": account})


@login_required
def delete(request):
    if request.method == "POST":
        account = Account.objects.select_related("account_type").get(uuid=request.POST.get("account_uuid"))

        # if account.user != request.user:
        #     return set_message_and_redirect(
        #         request,
        #         "f|You don't have access to delete this account.",
        #         reverse("blackbook:accounts", kwargs={"account_type", account.account_type.slug}),
        #     )

        account.delete()

        # Delete all "hanging" journal entries (no transactions linked)
        hanging_journal_entries = TransactionJournalEntry.objects.filter(transactions=None)
        hanging_journal_entries.delete()

        return set_message_and_redirect(
            request,
            's|Account "{account.name}" was succesfully deleted.'.format(account=account),
            reverse("blackbook:accounts", kwargs={"account_type": account.account_type.slug}),
        )

    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this.", reverse("blackbook:dashboard"))
