from django.urls import path

from .views import dashboard, profile, accounts, transactions, categories, tags

app_name = "blackbook"
urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path("profile/", profile.profile, name="profile"),
    path("update_exchange_rates/", dashboard.update_exchange_rates, name="update_exchange_rates"),
    #
    # Account Types
    path("accounts/add/", accounts.add_edit, name="accounts_add"),
    path("accounts/edit/<str:account_name>/", accounts.add_edit, name="accounts_edit"),
    path("accounts/delete/", accounts.delete, name="accounts_delete"),
    path("accounts/<str:account_type>/", accounts.accounts, name="accounts"),
    path("accounts/<str:account_type>/<str:account_name>/", accounts.accounts, name="accounts"),
    #
    # Transactions
    path("transactions/", transactions.transactions, name="transactions"),
    path("transactions/add/", transactions.add_edit, name="transactions_add"),
    path("transactions/edit/<str:transaction_uuid>/", transactions.add_edit, name="transactions_edit"),
    path("transactions/delete/", transactions.delete, name="transactions_delete"),
    path("journal_entries/edit/<str:journal_entry_uuid>/", transactions.journal_entry_edit, name="journal_entries_edit"),
    path("journal_entries/delete/", transactions.journal_entry_delete, name="journal_entries_delete"),
    #
    # Categories
    path("categories/", categories.categories, name="categories"),
    path("categories/add/", categories.categories, name="categories_add"),
    path("categories/edit/", categories.categories, name="categories_edit"),
    path("categories/delete/", categories.delete, name="categories_delete"),
    #
    # Tags
    path("tags/", tags.tags, name="tags"),
    path("tags/edit/", tags.tags, name="tags_edit"),
    path("tags/delete/", tags.delete, name="tags_delete"),
]