from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ...models import Category, get_default_currency
from ..serializers import CategorySerializer
from ..filters import IsOwnerFilterBackend
from ..permissions import IsOwner


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated & IsOwner]
    queryset = Category.objects.all()
    filter_backends = [IsOwnerFilterBackend, filters.SearchFilter]
    search_fields = ["name"]
    ordering = ["name"]

    @action(detail=True)
    def total(self, request, pk):
        default_currency = get_default_currency(self.request.user)

        currency = request.GET.get("currency", default_currency)

        category = self.get_object()
        total = category.total_in_currency(currency=currency)

        return Response({"id": category.id, "name": category.name, "currency": currency, "total": total.amount}, status=status.HTTP_200_OK)