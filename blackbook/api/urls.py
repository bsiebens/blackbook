from django.urls import path

from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from .views import users, accounts, transactions, categories, budgets

router = routers.DefaultRouter()
router.register(r"users", users.UserViewSet)
router.register(r"profile", users.ProfileViewSet)
router.register(r"accounts", accounts.AccountViewSet)
router.register(r"account_types", accounts.AccountTypeViewSet)
router.register(r"journal", transactions.TransactionJournalViewSet)
router.register(r"categories", categories.CategoryViewSet)
router.register(r"budgets", budgets.BudgetViewSet)

urlpatterns = router.urls