from django import forms
from django.utils import timezone

from djmoney.forms.fields import MoneyField
from djmoney.forms.widgets import MoneyWidget
from taggit.forms import TagField

from .models import get_currency_choices, get_default_currency, Budget, Account, TransactionJournalEntry, Category, AccountType


class ListModelChoiceField(forms.ChoiceField):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super(ListModelChoiceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None

        try:
            value = self.model.objects.get(id=value)
        except self.model.DoesNotExist:
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice")

        return value

    def valid_value(self, value):
        if self.required:
            if any(value.id == int(choice[0]) for choice in self.choices):
                return True

            return False

        else:
            return True


class BulmaMoneyWidget(MoneyWidget):
    template_name = "blackbook/forms/bulmamoneywidget.html"


class AccountForm(forms.ModelForm):
    starting_balance = forms.DecimalField(max_digits=15, decimal_places=2, required=False, initial=0.0)
    account_type = ListModelChoiceField(model=AccountType, choices=[(account_type.id, account_type) for account_type in AccountType.objects.all()])

    class Meta:
        model = Account
        fields = ["name", "account_type", "active", "include_in_net_worth", "include_on_dashboard", "iban", "currency", "virtual_balance"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class UserProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    default_currency = forms.ChoiceField(choices=get_currency_choices())
    default_period = forms.ChoiceField(choices=Budget.Period.choices)


class TransactionForm(forms.Form):
    description = forms.CharField()
    date = forms.DateField(initial=timezone.now)
    transaction_type = forms.ChoiceField()
    amount = MoneyField(widget=BulmaMoneyWidget())
    category = ListModelChoiceField(model=Category, required=False)
    budget = ListModelChoiceField(model=Budget, required=False)
    tags = forms.CharField(required=False, help_text="A list of comma separated tags.")
    from_account = ListModelChoiceField(model=Account, required=False)
    to_account = ListModelChoiceField(model=Account, required=False)
    add_new = forms.BooleanField(required=False, initial=False, help_text="After saving, display this form again to add an additional transaction.")

    def __init__(self, user, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)

        account_choices = [(account.id, account) for account in Account.objects.filter(user=user).filter(active=True)]
        account_choices.insert(0, (None, ""))
        category_choices = [(category.id, category) for category in Category.objects.filter(user=user)]
        category_choices.insert(0, (None, ""))
        budget_choices = [(budget.id, budget) for budget in Budget.objects.filter(user=user)]
        budget_choices.insert(0, (None, ""))

        self.fields["category"].choices = category_choices
        self.fields["budget"].choices = budget_choices
        self.fields["from_account"].choices = account_choices
        self.fields["to_account"].choices = account_choices
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
