from django.contrib.auth import get_user_model

from graphene_django import DjangoObjectType
from graphene_django.forms.mutation import DjangoModelFormMutation

import graphene

from ..forms import CategoryForm
from ..models import Category


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category

    @classmethod
    def get_queryset(cls, queryset, info):
        if info.context.user.is_anonymous:
            return Exception("Not logged in")

        return queryset.filter(user=info.context.user)