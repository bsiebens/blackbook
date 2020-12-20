from django.shortcuts import render, get_object_or_404

from ..models import AccountType, Account

def accounts(request, account_type):
    account_type = get_object_or_404(AccountType, slug=account_type)
    accounts = Account.objects.filter(account_type=account_type).filter(user=request.user)

    return render(request, "blackbook/accounts/account_type_list.html", {"account_type": account_type, "accounts": accounts}) 