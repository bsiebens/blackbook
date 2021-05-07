from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from djmoney.money import Money
from decimal import Decimal
from datetime import timedelta

from ..models import get_default_value, get_default_currency, TransactionJournal, Transaction, Account, BudgetPeriod
from ..utilities import calculate_period, display_period
from ..charts import AccountChart


@login_required
def dashboard(request):
    period = get_default_value(key="default_period", default_value="month", user=request.user)
    currency = get_default_currency(user=request.user)

    net_worth_transactions = (
        Transaction.objects.filter(account__active=True)
        .filter(account__net_worth=True)
        .filter(journal__date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True))
        .filter(amount_currency=currency)
        .select_related("journal")
        .select_related("account")
        .order_by("journal__date")
    )

    budgets = (
        BudgetPeriod.objects.filter(start_date__lte=timezone.localdate())
        .filter(end_date__gte=timezone.localdate())
        .filter(amount_currency=currency)
        .filter(budget__active=True)
        .aggregate(total=Coalesce(Sum("amount"), Decimal(0)), used=Coalesce(Sum("transactions__amount"), Decimal(0)))
    )

    accounts = Account.objects.filter(active=True).filter(net_worth=True).filter(dashboard=True).prefetch_related("transactions")

    data = {
        "totals": {
            "period": {
                "in": Money(0, currency),
                "out": Money(0, currency),
                "total": Money(0, currency),
            },
            "net_worth": Money(
                Transaction.objects.filter(account__active=True)
                .filter(account__net_worth=True)
                .filter(amount_currency=currency)
                .aggregate(total=Coalesce(Sum("amount"), Decimal(0)))["total"],
                currency,
            ),
        },
        "budget": {
            "total": Money(budgets["total"], currency),
            "available": Money(0, currency),
            "used": abs(Money(budgets["used"], currency)),
            "per_day": Money(0, currency),
        },
        "period": display_period(periodicty=period, start_date=timezone.localdate()),
        "charts": {
            "account_chart": AccountChart(
                data=net_worth_transactions.filter(account__dashboard=True),
                accounts=accounts,
                start_date=calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"],
                end_date=calculate_period(periodicity=period, start_date=timezone.localdate())["end_date"],
                user=request.user,
            ).generate_json()
        },
    }

    for transaction in net_worth_transactions:
        if transaction.amount.amount < 0:
            data["totals"]["period"]["out"] += transaction.amount
        else:
            data["totals"]["period"]["in"] += transaction.amount

    data["totals"]["period"]["total"] = data["totals"]["period"]["in"] + data["totals"]["period"]["out"]
    data["budget"]["available"] = data["budget"]["total"] - data["budget"]["used"]
    data["budget"]["per_day"] = (
        data["budget"]["used"]
        / (
            calculate_period(periodicity=period, start_date=timezone.localdate())["end_date"]
            - calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"]
        ).days
    )

    start_date = calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"] - timedelta(days=1)
    total_virtual_balance = Money(0, currency)
    for account in accounts:
        if account.currency == currency:
            data["totals"]["net_worth"] += account.balance_until_date(date=start_date)
            total_virtual_balance += Money(account.virtual_balance, currency)

    data["totals"]["net_worth"] -= total_virtual_balance

    return render(request, "blackbook/dashboard.html", {"data": data})