from django.shortcuts import render

from ..models import AccountType

def accounts(request, account_type):
    accounts = AccountType.objects.filter(slug=account_type).filter(accounts__user=request.user)

    return render(request, "blackbook/accounts/account_type_list.html", {"accounts": accounts}) 