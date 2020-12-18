from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_list_or_404
from django.urls import reverse
from django.utils import timezone

from djmoney.money import Money
from djmoney.contrib.exchange.backends import OpenExchangeRatesBackend
from djmoney.contrib.exchange.models import convert_money

from ..models import get_default_currency, Account, BudgetPeriod, Category, TransactionJournalEntry
from ..utilities import display_period, calculate_period, set_message_and_redirect
from ..charts import AccountChart


def update_exchange_rates(request):
    OpenExchangeRatesBackend().update_rates()

    return set_message_and_redirect(
        request, "s|Exchange rates have been updated from Open Exchange Rates.", request.GET.get("next", reverse("blackbook:dashboard"))
    )


@login_required
def dashboard(request):
    accounts = Account.objects.filter(user=request.user).filter(active=True).prefetch_related("transactions")
    budgets = BudgetPeriod.objects.filter(budget__user=request.user).filter(start_date__lte=timezone.now()).filter(end_date__gte=timezone.now())
    period = request.user.userprofile.default_period
    currency = get_default_currency(user=request.user)

    data = {
        "totals": {
            "period": {
                "in": Money(0, currency),
                "out": Money(0, currency),
                "total": Money(0, currency),
            },
            "net_worth": Money(0, currency),
        },
        "period": display_period(periodicty=period),
        "budget": {"available": Money(0, currency), "used": Money(0, currency), "per_day": None},
        "budgets": budgets,
        "categories": Money(sum([category.total.amount for category.total in Category.objects.filter(user=request.user)]), currency),
        "charts": {
            "account_chart": AccountChart(
                data=accounts,
                start_date=calculate_period(periodicity=period)["start_date"],
                end_date=calculate_period(periodicity=period)["end_date"],
                user=request.user,
            ).generate_json()
        },
        "transactions": TransactionJournalEntry.objects.filter(user=request.user)
        .filter(date__range=calculate_period(periodicity=period, as_tuple=True))
        .order_by("-date")
        .order_by("-created"),
        "currency": currency,
    }

    for account in accounts:
        data["totals"]["period"]["in"] += convert_money(account.total_in_for_period(), currency)
        data["totals"]["period"]["out"] += convert_money(account.total_out_for_period(), currency)

    for account in accounts.filter(include_in_net_worth=True):
        data["totals"]["net_worth"] += convert_money(account.balance, currency)

    for budget in budgets:
        data["budget"]["available"] += convert_money(budget.available(), currency)
        data["budget"]["used"] += convert_money(budget.used(), currency)
    data["budget"]["per_day"] = (
        data["budget"]["used"] / (calculate_period(periodicity=period)["end_date"] - calculate_period(periodicity=period)["start_date"]).days * -1
    )

    data["totals"]["period"]["total"] = data["totals"]["period"]["in"] + data["totals"]["period"]["out"]

    return render(request, "blackbook/dashboard.html", {"data": data})