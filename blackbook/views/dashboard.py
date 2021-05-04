from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from djmoney.money import Money
from decimal import Decimal
from datetime import timedelta

from ..models import get_default_value, get_default_currency, Transaction, Account
from ..utilities import calculate_period, display_period
from ..charts import AccountChart


@login_required
def dashboard(request):
    period = get_default_value(key="default_period", default_value="month", user=request.user)
    currency = get_default_currency(user=request.user)

    net_worth_transactions = (
        Transaction.objects.filter(account__active=True)
        .filter(account__net_worth=True)
        .filter(account__dashboard=True)
        .filter(journal__date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True))
        .filter(amount_currency=currency)
        .select_related("journal")
        .select_related("account")
        .annotate(total=Coalesce(Sum("amount"), Decimal(0)))
        .order_by("journal__date")
    )

    accounts = Account.objects.filter(active=True).filter(net_worth=True).filter(dashboard=True).prefetch_related("transactions")

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
        "charts": {
            "account_chart": AccountChart(
                data=net_worth_transactions,
                start_date=calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"],
                end_date=calculate_period(periodicity=period, start_date=timezone.localdate())["end_date"],
                user=request.user,
            ).generate_json()
        },
    }

    for transaction in net_worth_transactions:
        amount = Money(transaction.total, currency)

        if amount.amount < 0:
            data["totals"]["period"]["out"] += amount
        else:
            data["totals"]["period"]["in"] += amount

        data["totals"]["net_worth"] += amount

    data["totals"]["period"]["total"] = data["totals"]["period"]["in"] + data["totals"]["period"]["out"]

    start_date = calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"] - timedelta(days=1)
    total_virtual_balance = Money(0, currency)
    for account in accounts:
        if account.currency == currency:
            data["totals"]["net_worth"] += account.balance_until_date(date=start_date)
            total_virtual_balance += Money(account.virtual_balance, currency)

    data["totals"]["net_worth"] -= total_virtual_balance

    return render(request, "blackbook/dashboard.html", {"data": data})