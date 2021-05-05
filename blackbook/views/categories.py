from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..forms import CategoryForm
from ..models import Category
from ..utilities import set_message_and_redirect


@login_required
def categories(request):
    categories = Category.objects.all()

    forms = []
    for category in categories:
        forms.append(CategoryForm(None, instance=category))

    category_form = CategoryForm(None, instance=Category())
    category_uuid = None

    if request.POST:
        uuid = request.POST.get("category_uuid", None)

        if uuid is not None:
            category = categories.get(uuid=uuid)
            category_form = CategoryForm(request.POST, instance=category)

            if category_form.is_valid():
                category = category_form.save()

                return set_message_and_redirect(
                    request, 's|Category "{category.name}" was updated succesfully.'.format(category=category), reverse("blackbook:categories")
                )

            category_uuid = category.uuid

            for form in forms:
                if form.instance == category:
                    forms[forms.index(form)] = category_form

        else:
            category_form = CategoryForm(request.POST, instance=Category())

            if category_form.is_valid():
                category = category_form.save()

                return set_message_and_redirect(
                    request, 's|Category "{category.name}" was saved succesfully.'.format(category=category), reverse("blackbook:categories")
                )

            category_uuid = "add"

    return render(
        request,
        "blackbook/categories/list.html",
        {"categories": categories, "forms": forms, "category_form": category_form, "category_uuid": category_uuid},
    )


@login_required
def delete(request):
    if request.method == "POST":
        category = get_object_or_404(Category, uuid=request.POST.get("category_uuid"))

        category.delete()
        return set_message_and_redirect(
            request, 's|Category "{category.name}" was succesfully deleted.'.format(category=category), reverse("blackbook:categories")
        )

    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this.", reverse("blackbook:categories"))
