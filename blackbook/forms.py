from django import forms
from django.utils import timezone

from djmoney.forms.fields import MoneyField
from djmoney.forms.widgets import MoneyWidget
from taggit.forms import TagField

from .models import get_currency_choices, get_default_currency, Budget, Account, TransactionJournalEntry, Category


class BulmaMoneyWidget(MoneyWidget):
    template_name = "blackbook/forms/bulmamoneywidget.html"


class AccountForm(forms.ModelForm):
    starting_balance = forms.DecimalField(max_digits=15, decimal_places=2, required=False, initial=0.0)

    class Meta:
        model = Account
        fields = ["name", "account_type", "active", "include_in_net_worth", "iban", "currency", "virtual_balance"]


class UserProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    default_currency = forms.ChoiceField(choices=get_currency_choices())
    default_period = forms.ChoiceField(choices=Budget.Period.choices)


class TransactionForm(forms.Form):
    description = forms.CharField()
    date = forms.DateField(initial=timezone.now)
    transaction_type = forms.ChoiceField(choices=TransactionJournalEntry.TransactionType.choices)
    amount = MoneyField(widget=BulmaMoneyWidget())
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, blank=True)
    budget = forms.ModelChoiceField(queryset=Budget.objects.all(), required=False, blank=True)
    tags = forms.CharField(required=False, help_text="A list of comma separated tags.")
    from_account = forms.ModelChoiceField(queryset=Account.objects.all(), required=False, blank=True)
    to_account = forms.ModelChoiceField(queryset=Account.objects.all(), required=False, blank=True)
    add_new = forms.BooleanField(required=False, initial=False, help_text="After saving, display this form again to add an additional transaction.")

    def __init__(self, user, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)

        accounts = Account.objects.filter(user=user).filter(active=True)

        self.fields["category"].queryset = Category.objects.filter(user=user)
        self.fields["budget"].queryset = Budget.objects.filter(user=user)
        self.fields["to_account"].queryset = accounts
        self.fields["from_account"].queryset = accounts
        self.fields["amount"].initial = ["0", get_default_currency(user=user)]

        self.fields["transaction_type"].choices = [
            (k, v) for k, v in TransactionJournalEntry.TransactionType.choices if k != TransactionJournalEntry.TransactionType.START
        ]

    def clean(self):
        cleaned_data = super().clean()

        transaction_type = cleaned_data.get("transaction_type")

        if transaction_type in [
            TransactionJournalEntry.TransactionType.START,
            TransactionJournalEntry.TransactionType.DEPOSIT,
            TransactionJournalEntry.TransactionType.RECONCILIATION,
        ]:
            if cleaned_data.get("to_account") is None:
                self.add_error("transaction_type", "To Account must be supplied for this transaction type.")
                self.add_error("to_account", "To Account must be supplied for this transaction type.")

        elif transaction_type == TransactionJournalEntry.TransactionType.WITHDRAWAL:
            if cleaned_data.get("from_account") is None:
                self.add_error("transaction_type", "From Account must be supplied for this transaction type.")
                self.add_error("from_account", "From Account must be supplied for this transaction type.")

        else:
            if cleaned_data.get("to_account") is None or cleaned_data.get("from_account") is None:
                self.add_error("transaction_type", "To and From Account must be supplied for this transaction type.")
                self.add_error("to_account", "To and From Account must be supplied for this transaction type.")
                self.add_error("from_account", "To and From Account must be supplied for this transaction type.")
