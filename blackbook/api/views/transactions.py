from rest_framework import viewsets, filters, mixins
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from djmoney.money import Money

from ...models import TransactionJournalEntry, Transaction
from ..serializers import JournalEntrySerializer
from ..permissions import IsOwner
from ..filters import IsOwnerFilterBackend, TagsFilter


class TransactionJournalViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated & IsOwner]
    queryset = TransactionJournalEntry.objects.all()
    filter_backends = [IsOwnerFilterBackend, filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend, TagsFilter]
    filterset_fields = ["category", "budget", "amount_currency"]
    search_fields = ["description"]
    ordering_fields = ["date", "created"]
    ordering = ["date", "created"]