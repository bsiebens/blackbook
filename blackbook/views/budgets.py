from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..forms import BudgetForm
from ..models import Budget
from ..utilities import set_message_and_redirect


@login_required
def budgets(request):
    budgets = Budget.objects.all()

    forms = []
    for budget in budgets:
        forms.append(BudgetForm(None, instance=budget))

    budget_form = BudgetForm(None, instance=Budget())
    budget_uuid = None

    if request.POST:
        uuid = request.POST.get("budget_uuid", None)

        if uuid is not None:
            budget = budgets.get(uuid=uuid)
            budget_form = BudgetForm(request.POST, instance=budget)

            if budget_form.is_valid():
                budget = budget_form.save()

                return set_message_and_redirect(
                    request, 's|Budget "{budget.name}" was updated succesfully.'.format(budget=budget), reverse("blackbook:budgets")
                )

            budget_uuid = budget.uuid

            for form in forms:
                if form.instance == budget:
                    forms[forms.index(form)] = budget_form

        else:
            budget_form = BudgetForm(request.POST, instance=Budget())

            if budget_form.is_valid():
                budget = budget_form.save()

                return set_message_and_redirect(
                    request, 's|Budget "{budget.name}" was saved succesfully.'.format(budget=budget), reverse("blackbook:budgets")
                )

            budget_uuid = "add"

    return render(
        request, "blackbook/budgets/list.html", {"budgets": budgets, "forms": forms, "budget_form": budget_form, "budget_uuid": budget_uuid}
    )


@login_required
def delete(request):
    if request.method == "POST":
        budget = get_object_or_404(Budget, uuid=request.POST.get("budget_uuid"))

        budget.delete()
        return set_message_and_redirect(
            request, 's|Budget "{budget.name}" was succesfully deleted.'.format(budget=budget), reverse("blackbook:budgets")
        )

    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this.", reverse("blackbook:budgets"))