from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from taggit.models import Tag

from ..models import TransactionJournalEntry
from ..forms import TagForm
from ..utilities import set_message_and_redirect


@login_required
def tags(request):
    transactions = TransactionJournalEntry.objects.filter(user=request.user)
    tags = Tag.objects.filter(transactionjournalentry__in=transactions)

    forms = []
    for tag in tags:
        forms.append(TagForm(None, instance=tag))

    tag_id = None
    if request.POST:
        tag = Tag.objects.get(pk=request.POST.get("tag_id", None))
        tag_id = tag.id
        tag_form = TagForm(request.POST, instance=tag)

        if tag_form.is_valid():
            tag = tag_form.save()

            return set_message_and_redirect(request, 's|Tag "{tag.name}" was updated succesfully.'.format(tag=tag), reverse("blackbook:tags"))

        for form in forms:
            if form.instance == tag:
                forms[forms.index(form)] = tag_form

    return render(request, "blackbook/tags/list.html", {"tags": tags, "forms": forms, "tag_id": tag_id})


@login_required
def delete(request):
    if request.method == "POST":
        tag = get_object_or_404(Tag, pk=request.POST.get("tag_id"))

        transactions = TransactionJournalEntry.objects.filter(tags__id__contains=tag.id)

        for transaction in transactions:
            transaction.tags.remove(tag)

        return set_message_and_redirect(request, 's|Tag "{tag.name}" was succesfully deleted.'.format(tag=tag), reverse("blackbook:tags"))
    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this.", reverse("blackbook:tags"))
