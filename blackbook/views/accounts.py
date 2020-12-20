from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..models import AccountType, Account
from ..utilities import set_message_and_redirect
from ..forms import AccountForm


@login_required
def accounts(request, account_type, account_name=None):
    if account_name is not None:
        account = get_object_or_404(Account, slug=account_name)

        if account.user != request.user:
            return set_message_and_redirect(
                request, "f|You don't have access to this account.", reverse("blackbook:accounts", kwargs={"account_type": account_type})
            )

    else:
        account_type = get_object_or_404(AccountType, slug=account_type)
        accounts = Account.objects.filter(account_type=account_type).filter(user=request.user)

        return render(request, "blackbook/accounts/account_type_list.html", {"account_type": account_type, "accounts": accounts})


@login_required
def account_add_edit(request, account_name=None):
    account = Account()

    if account_name is not None:
        account = get_object_or_404(Account, slug=account_name)

        if account.user != request.user:
            return set_message_and_redirect(
                request, "f|You don't have access to this account.", reverse("blackbook:accounts", kwargs={"account_type": account_type})
            )

    account_form = AccountForm(request.POST or None, instance=account)

    if request.POST and account_form.is_valid():
        account = account_form.save(commit=False)
        account.user = request.user
        account.save()

        return set_message_and_redirect(
            request,
            's|Account "{account.name}" was saved succesfully.'.format(account=account),
            reverse("blackbook:accounts", kwargs={"account_type": account.account_type.slug}),
        )

    return render(request, "blackbook/accounts/account_form.html", {"account_form": account_form, "account": account})


@login_required
def delete(request):
    if request.method == "POST":
        account = Account.objects.select_related("account_type").get(pk=request.POST.get("account_id"))

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
