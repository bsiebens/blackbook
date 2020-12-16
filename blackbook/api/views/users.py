from django.contrib.auth.models import User

from rest_framework import status, viewsets
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from ..serializers import UserSerializer, ProfileSerializer
from ..permissions import IsOwner
from ..filters import IsOwnerFilterBackend
from ...models import UserProfile


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]
    queryset = User.objects.all()


class ProfileViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated & IsOwner]
    queryset = UserProfile.objects.all()
    filter_backends = [IsOwnerFilterBackend]