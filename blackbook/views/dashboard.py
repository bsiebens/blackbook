from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Q
from django.utils import timezone

from djmoney.money import Money

from ..models import get_default_value, get_default_currency, Transaction
from ..utilities import calculate_period


@login_required
def dashboard(request):
    period = get_default_value(key="default_period", default_value="month", user=request.user)
    currency = get_default_currency(user=request.user)

    transactions = (
        Transaction.objects.filter(Q(source_account__active=True) | Q(destination_account__active=True))
        .filter(Q(source_account__net_worth=True) | Q(destination_account__net_worth=True))
        .filter(journal__date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True))
    )

    data = {}

    return render(request, "blackbook/dashboard.html", {"data": data})