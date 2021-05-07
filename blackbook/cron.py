from django.utils import timezone

from .models import Budget, BudgetPeriod
from .utilities import calculate_period


def create_budget_periods():
    budgets = (
        Budget.objects.filter(active=True)
        .exclude(auto_budget=Budget.AutoBudget.NO)
        .filter(budgetperiods__end_date__lt=timezone.localdate())
        .exclude(budgetperiods__start_date__lte=timezone.localdate(), budgetperiods__end_date__gte=timezone.localdate())
    )

    for budget in budgets:
        amount_to_add = budget.amount

        if budget.auto_budget == Budget.AutoBudget.ADD:
            amount_to_add += budget.budgetperiods.last().available

        period = calculate_period(periodicity=budget.auto_budget_period, start_date=timezone.localdate())
        budget.budgetperiods.create(start_date=period["start_date"], end_date=period["end_date"], amount=amount_to_add)
