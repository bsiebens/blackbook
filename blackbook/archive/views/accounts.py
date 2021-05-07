from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum, Prefetch, Count
from django.db.models.functions import Coalesce
from django.utils import timezone

from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money

from ..models import AccountType, Account, TransactionJournalEntry, Transaction, get_default_currency
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
                "journal_entry__from_account__account_type__category",
            )
            .annotate(total=Sum("amount"))
            .order_by("-journal_entry__date", "-journal_entry__created")
        )

        if len(transactions) == 0:
            transactions = [
                {
                    "amount_currency": account.currency,
                    "negative": None,
                    "account__name": account.name,
                    "account__virtual_balance": account.virtual_balance,
                    "journal_entry": None,
                    "journal_entry__date": timezone.localdate(),
                    "journal_entry__transaction_type": None,
                    "journal_entry__budget__budget__name": None,
                    "journal_entry__category__name": None,
                    "journal_entry__from_account__name": None,
                    "journal_entry__from_account__account_type__category": None,
                    "total": 0,
                }
            ]

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
            "income_chart_count": len([item for item in transactions if not item["negative"] and item["negative"] is not None]),
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
        account_types = (
            AccountType.objects.filter(category=account_type)
            .annotate(count=Count("accounts"))
            .filter(count__gt=0)
            .prefetch_related(Prefetch("accounts", Account.objects.annotate(total=Coalesce(Sum("transactions__amount"), 0))))
        )
        accounts = Account.objects.filter(account_type__category=account_type).annotate(total=Coalesce(Sum("transactions__amount"), 0))
        currency = get_default_currency(request.user)

        for account_type in account_types:
            account_type.total = Money(0, currency)

            for account in account_type.accounts.all():
                account.total -= account.virtual_balance

                account_type.total += convert_money(Money(account.total, account.currency), currency)

        return render(
            request,
            "blackbook/accounts/list.html",
            {"account_type": account_type, "account_types": account_types, "accounts": accounts},
        )


@login_required
def add_edit(request, account_name=None):
    account = Account()

    if account_name is not None:
        account = get_object_or_404(Account, slug=account_name)

    account_form = AccountForm(request.POST or None, instance=account, initial={"starting_balance": account.starting_balance.amount})

    if request.POST and account_form.is_valid():
        account = account_form.save(commit=False)
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
            reverse("blackbook:accounts", kwargs={"account_type": account.account_type.category, "account_name": account.slug}),
        )

    return render(request, "blackbook/accounts/form.html", {"account_form": account_form, "account": account})


@login_required
def delete(request):
    if request.method == "POST":
        account = Account.objects.select_related("account_type").get(uuid=request.POST.get("account_uuid"))

        account.delete()

        # Delete all "hanging" journal entries (no transactions linked)
        hanging_journal_entries = TransactionJournalEntry.objects.filter(transactions=None)
        hanging_journal_entries.delete()

        return set_message_and_redirect(
            request,
            's|Account "{account.name}" was succesfully deleted.'.format(account=account),
            reverse("blackbook:accounts", kwargs={"account_type": account.account_type.category}),
        )

    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this.", reverse("blackbook:dashboard"))
