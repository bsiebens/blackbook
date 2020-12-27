from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..forms import CategoryForm
from ..models import Category
from ..utilities import set_message_and_redirect


@login_required
def categories(request):
    categories = Category.objects.filter(user=request.user)
    
    forms = []
    for category in categories:
        forms.append(CategoryForm(None, instance=category))

    category_uuid = None

    if request.POST:
        category = categories.get(uuid=request.POST["category_uuid"])
        category_form = CategoryForm(request.POST, instance=category)

        if category_form.is_valid():
            category = category_form.save()

            return set_message_and_redirect(request, 's|Category "{category.name}" was updated succesfully.'.format(category=category), reverse("blackbook:categories"))
        
        category_uuid = request.POST["category_uuid"]

    return render(request, "blackbook/categories/list.html", {"categories": categories, "forms": forms, "category_uuid": category_uuid})


@login_required
def add_edit(request, category_uuid):
    pass


@login_required
def delete(request):
    pass