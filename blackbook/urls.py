from django.urls import path

from .views import dashboard, profile, accounts

app_name = "blackbook"
urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path("profile/", profile.profile, name="profile"),
    path("update_exchange_rates/", dashboard.update_exchange_rates, name="update_exchange_rates"),
    #
    # Account Types
    path("accounts/add/", accounts.account_add_edit, name="accounts_add"),
    path("accounts/edit/<str:account_name>/", accounts.account_add_edit, name="accounts_edit"),
    path("accounts/delete/", accounts.delete, name="accounts_delete"),
    path("accounts/<str:account_type>/", accounts.accounts, name="accounts"),
    path("accounts/<str:account_type>/<str:account_name>/", accounts.accounts, name="accounts"),
]