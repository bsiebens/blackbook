from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..models import AccountType, Account
from ..utilities import set_message_and_redirect

@login_required
def accounts(request, account_type):
    account_type = get_object_or_404(AccountType, slug=account_type)
    accounts = Account.objects.filter(account_type=account_type).filter(user=request.user)

    return render(request, "blackbook/accounts/account_type_list.html", {"account_type": account_type, "accounts": accounts})

@login_required
def delete(request):
    if request.method == "POST":
        account = get_object_or_404(Account, pk=request.POST.get("account_id")).select_related("account_type")

        if account.user != request.user:
            return set_message_and_redirect(request, "f|You don't have access to delete this account.", reverse("blackbook:accounts", kwargs={"account_type", account.account_type.slug}))
        
        account.delete()
        return set_message_and_redirect(request, "s|Account {account.name} was succesfully deleted.".format(account=account), reverse("blackbook:accounts", kwargs={"account_type": account.account_type.slug}))