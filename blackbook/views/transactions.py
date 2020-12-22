from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..models import TransactionJournalEntry, Transaction
from ..utilities import set_message_and_redirect


@login_required
def delete(request):
    if request.method == "POST":
        transaction = (
            Transaction.objects.select_related("journal_entry").select_related("account__account_type").get(uuid=request.POST.get("transaction_uuid"))
        )

        if transaction.journal_entry.user != request.user:
            return set_message_and_redirect(
                request,
                "f|You don't have access to delete this transaction.",
                reverse(
                    "blackbook:accounts", kwargs={"account_type": transaction.account.account_type.slug, "account_name": transacion.account.slug}
                ),
            )

        transaction.journal_entry.delete()
        return set_message_and_redirect(
            request,
            's|Transaction "{transaction.journal_entry.description}" was succesfully deleted.'.format(transaction=transaction),
            reverse("blackbook:accounts", kwargs={"account_type": transaction.account.account_type.slug, "account_name": transaction.account.slug}),
        )

    else:
        return set_message_and_redirect(
            request,
            "w|You are not allowed to access this page like this.",
            reverse("blackbook:accounts", kwargs={"account_type": transaction.account.account_type.slug, "account_name": transaction.account.slug}),
        )
