from rest_framework import permissions

from ..models import BudgetPeriod


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if type(obj) == BudgetPeriod:
            return obj.budget.user == request.user

        return obj.user == request.user