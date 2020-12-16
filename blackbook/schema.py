import graphene
import graphql_jwt

from .api import users


class Mutation(users.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    revoke_token = graphql_jwt.Revoke.Field()


class Query(users.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)