from django.utils import timezone

from rest_framework import viewsets, filters, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ...models import Account, AccountType
from ..serializers import AccountSerializer, AccountTypeSerializer
from ..filters import IsOwnerFilterBackend
from ..permissions import IsOwner


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated & IsOwner]
    queryset = Account.objects.all()
    filter_backends = [IsOwnerFilterBackend, filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["active", "include_in_net_worth", "currency", "account_type"]
    search_fields = ["name"]
    ordering_fields = ["name", "created", "account_type"]
    ordering = ["name", "created"]

    @action(detail=True)
    def balance_until(self, request, pk):
        date = request.GET.get("date", timezone.now().date())

        account = self.get_object()
        total = account.balance_until_date(date)

        return Response({"date": date, "total": total.amount, "total_currency": str(total.currency)}, status=status.HTTP_200_OK)

    @action(detail=True)
    def total_in_for_period(self, request, pk):
        period = request.GET.get("period", "month")
        start_date = request.GET.get("date", timezone.now().date())

        account = self.get_object()
        total = account.total_in_for_period(period=period, start_date=start_date)

        return Response(
            {"date": start_date, "period": period, "total": total.amount, "total_currency": str(total.currency)}, status=status.HTTP_200_OK
        )

    @action(detail=True)
    def total_out_for_period(self, request, pk):
        period = request.GET.get("period", "month")
        start_date = request.GET.get("date", timezone.now().date())

        account = self.get_object()
        total = account.total_out_for_period(period=period, start_date=start_date)

        return Response(
            {"date": start_date, "period": period, "total": total.amount, "total_currency": str(total.currency)}, status=status.HTTP_200_OK
        )

    @action(detail=True)
    def balance_for_period(self, request, pk):
        period = request.GET.get("period", "month")
        start_date = request.GET.get("date", timezone.now().date())

        account = self.get_object()
        total = account.balance_for_period(period=period, start_date=start_date)

        return Response(
            {"date": start_date, "period": period, "total": total.amount, "total_currency": str(total.currency)}, status=status.HTTP_200_OK
        )


class AccountTypeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AccountTypeSerializer
    permission_classes = [IsAuthenticated]

    queryset = AccountType.objects.all()