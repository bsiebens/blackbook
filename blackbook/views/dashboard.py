from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_list_or_404
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum

from djmoney.money import Money
from djmoney.contrib.exchange.backends import OpenExchangeRatesBackend
from djmoney.contrib.exchange.models import convert_money

from ..models import get_default_currency, Account, BudgetPeriod, Category, TransactionJournalEntry, Transaction
from ..utilities import display_period, calculate_period, set_message_and_redirect
from ..charts import AccountChart


def update_exchange_rates(request):
    OpenExchangeRatesBackend().update_rates()

    return set_message_and_redirect(
        request, "s|Exchange rates have been updated from Open Exchange Rates.", request.GET.get("next", reverse("blackbook:dashboard"))
    )


@login_required
def dashboard(request):
    period = request.user.userprofile.default_period
    currency = get_default_currency(user=request.user)

    totals = (
        Transaction.objects.filter(account__active=True)
        .filter(account__include_in_net_worth=True)
        .filter(journal_entry__date__range=calculate_period(period, start_date=timezone.localdate(), as_tuple=True))
        .values("amount_currency", "negative")
        .annotate(total=Sum("amount"))
    )
    net_worth = (
        Transaction.objects.filter(account__active=True)
        .filter(account__include_in_net_worth=True)
        .filter(journal_entry__date__range=calculate_period(period, start_date=timezone.localdate(), as_tuple=True))
        .select_related("journal_entry")
        .select_related("account")
        .values("amount_currency", "journal_entry__date", "account__name", "account__virtual_balance", "account__include_on_dashboard")
        .annotate(total=Sum("amount"))
        .order_by("journal_entry__date")
    )

    budgets = (
        BudgetPeriod.objects.filter(start_date__lte=timezone.now())
        .filter(end_date__gte=timezone.now())
        .values("amount_currency")
        .annotate(total=Sum("amount"))
    )
    budgets_used = (
        Transaction.objects.filter(account__active=True)
        .filter(negative=True)
        .filter(journal_entry__budget__start_date__lte=timezone.now())
        .filter(journal_entry__budget__end_date__gte=timezone.now())
        .values("amount_currency")
        .annotate(total=Sum("amount"))
    )

    accounts = Account.objects.filter(active=True).filter(include_in_net_worth=True).prefetch_related("transactions__journal_entry")

    data = {
        "totals": {
            "period": {
                "in": Money(0, currency),
                "out": Money(0, currency),
                "total": Money(0, currency),
            },
            "net_worth": Money(0, currency),
        },
        "period": display_period(periodicty=period, start_date=timezone.localdate()),
        "budget": {"total": Money(0, currency), "available": Money(0, currency), "used": Money(0, currency), "per_day": None},
        "charts": {
            "account_chart": AccountChart(
                data=[item for item in net_worth if item["account__include_on_dashboard"]],
                start_date=calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"],
                end_date=calculate_period(periodicity=period, start_date=timezone.localdate())["end_date"],
                user=request.user,
            ).generate_json()
        },
    }

    for total in totals:
        if total["negative"]:
            data["totals"]["period"]["out"] += convert_money(Money(total["total"], total["amount_currency"]), currency)
        else:
            data["totals"]["period"]["in"] += convert_money(Money(total["total"], total["amount_currency"]), currency)
    data["totals"]["period"]["total"] = data["totals"]["period"]["in"] + data["totals"]["period"]["out"]

    for total in net_worth:
        data["totals"]["net_worth"] += convert_money(Money(total["total"], total["amount_currency"]), currency)

    total_virtual_balance = Money(0, currency)
    for account in accounts:
        total_virtual_balance += convert_money(Money(account.virtual_balance, account.currency), currency)
    data["totals"]["net_worth"] -= total_virtual_balance

    for budget in budgets:
        data["budget"]["total"] += convert_money(Money(budget["total"], budget["amount_currency"]), currency)

    for budget in budgets_used:
        data["budget"]["used"] += convert_money(Money(budget["total"], budget["amount_currency"]), currency)
    data["budget"]["available"] = data["budget"]["total"] + data["budget"]["used"]
    data["budget"]["per_day"] = (
        data["budget"]["used"]
        / (
            calculate_period(periodicity=period, start_date=timezone.localdate())["end_date"]
            - calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"]
        ).days
        * -1
    )

    return render(request, "blackbook/dashboard.html", {"data": data})