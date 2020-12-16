from django.utils import timezone

from rest_framework import viewsets, filters, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from djmoney.money import Money

from ...models import Budget, BudgetPeriod
from ..serializers import BudgetSerializer, BudgetPeriodSerializer
from ..permissions import IsOwner
from ..filters import IsOwnerFilterBackend
from ...utilities import calculate_period


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated & IsOwner]
    queryset = Budget.objects.all()
    filter_backends = [IsOwnerFilterBackend, filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ["auto_budget", "auto_budget_period", "active"]
    search_fields = ["name"]
    ordering = ["name"]

    @action(detail=True)
    def get_period(self, request, pk):
        date = request.GET.get("date", timezone.now().date())

        budget = self.get_object()
        period = budget.get_period_for_date(date=date)

        if period is not None:
            serializer = BudgetPeriodSerializer(period)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response("No period found", status=status.HTTP_404_NOT_FOUND)

    @action(detail=False)
    def calculate_period(self, request):
        period = request.GET.get("period", "month")
        start_date = request.GET.get("date", timezone.now().date())

        return Response(
            {
                "period": period,
                "start_date": calculate_period(period, start_date)["start_date"],
                "end_date": calculate_period(period, start_date)["end_date"],
            },
            status=status.HTTP_200_OK,
        )
