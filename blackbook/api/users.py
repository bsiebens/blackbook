from django.contrib.auth import get_user_model

from graphene_django import DjangoObjectType
from graphene_django.forms.mutation import DjangoFormMutation

import graphene

from ..forms import ProfileForm


class UserType(DjangoObjectType):
    default_currency = graphene.String(description="default currency")
    default_period = graphene.String(description="default period")

    class Meta:
        model = get_user_model()

    def resolve_default_currency(self, info):
        return self.userprofile.default_currency

    def resolve_default_period(self, info):
        return self.userprofile.default_period


class ProfileMutation(DjangoFormMutation):
    user = graphene.Field(UserType)

    class Meta:
        form_class = ProfileForm

    def perform_mutate(form, info):
        user = info.context.user

        if user.is_anonymous:
            return Exception("Not logged in")

        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.save()

        user.userprofile.default_currency = form.cleaned_data["currency"]
        user.userprofile.default_period = form.cleaned_data["period"]
        user.userprofile.save()

        return ProfileMutation(user=user)


class Mutation(graphene.ObjectType):
    update_user = ProfileMutation.Field()


class Query(graphene.ObjectType):
    profile = graphene.Field(UserType)

    def resolve_profile(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Not logged in")

        return user