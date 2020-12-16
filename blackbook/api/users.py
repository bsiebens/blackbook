from django.contrib.auth import get_user_model

import graphene
from graphene_django import DjangoObjectType


class UserType(DjangoObjectType):
    default_currency = graphene.String(description="default currency")
    default_period = graphene.String(description="default period")

    class Meta:
        model = get_user_model()

    def resolve_default_currency(self, info):
        return self.userprofile.default_currency

    def resolve_default_period(self, info):
        return self.userprofile.default_period


class UpdateProfile(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        default_period = graphene.String(required=False)
        default_currency = graphene.String(required=False)

    def mutate(self, info, default_period=None, default_currency=None):
        user = info.context.user

        if user.is_anonymous:
            raise Exception("Not logged in")

        if default_currency is not None:
            user.userprofile.default_currency = default_currency

        if default_period is not None:
            user.userprofile.default_period = default_period

        user.userprofile.save()
        return UpdateProfile(user=user)


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, username, password):
        user = get_user_model()(username=username)

        user.set_password(password)
        user.save()

        return CreateUser(user=user)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_profile = UpdateProfile.Field()


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Not logged in")

        return user