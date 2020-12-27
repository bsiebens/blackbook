from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..forms import CategoryForm
from ..models import Category
from ..utilities import set_message_and_redirect


@login_required
def categories(request):
    categories = Category.objects.filter(user=request.user)

    return render(request, "blackbook/categories/list.html", {"categories": categories})


@login_required
def add_edit(request, category_uuid):
    pass


@login_required
def delete(request):
    pass