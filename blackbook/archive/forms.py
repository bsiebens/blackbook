from django import forms
from django.utils import timezone, safestring

from djmoney.forms.fields import MoneyField
from djmoney.forms.widgets import MoneyWidget
from taggit.forms import TagField
from taggit.models import Tag

from .models import get_currency_choices, get_default_currency, Budget, Account, TransactionJournalEntry, Category, AccountType


class DateInput(forms.DateInput):
    input_type = "date"


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


class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({"list": "list__%s" % self._name})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name

        for item in self._list:
            data_list += '<option value="%s">%s</option>' % (item, item)

        data_list += "</datalist>"

        return safestring.mark_safe(text_html + data_list)


class BulmaMoneyWidget(MoneyWidget):
    template_name = "blackbook/forms/bulmamoneywidget.html"


class AccountForm(forms.ModelForm):
    starting_balance = forms.DecimalField(max_digits=15, decimal_places=2, required=False, initial=0.0)
    account_type = ListModelChoiceField(model=AccountType)

    class Meta:
        model = Account
        fields = ["name", "account_type", "active", "include_in_net_worth", "include_on_dashboard", "iban", "currency", "virtual_balance"]

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)

        self.fields["account_type"].choices = [(account_type.id, account_type) for account_type in AccountType.objects.all()]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]


class UserProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    default_currency = forms.ChoiceField(choices=get_currency_choices())
    default_period = forms.ChoiceField(choices=Budget.Period.choices)


class TransactionForm(forms.Form):
    description = forms.CharField()
    date = forms.DateField(initial=timezone.now, widget=DateInput)
    transaction_type = forms.ChoiceField(initial=TransactionJournalEntry.TransactionType.WITHDRAWAL)
    amount = MoneyField(widget=BulmaMoneyWidget())
    category = forms.CharField(required=False)
    budget = forms.CharField(required=False)
    tags = forms.CharField(required=False, help_text="A list of comma separated tags.")
    from_account = forms.CharField(required=False)
    to_account = forms.CharField(required=False)
    add_new = forms.BooleanField(required=False, initial=False, help_text="After saving, display this form again to add an additional transaction.")
    display = forms.BooleanField(required=False, initial=True, help_text="After saving, display this form again to review this transaction.")

    def __init__(self, user, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)

        account_choices = [(account.id, account) for account in Account.objects.filter(active=True).order_by("account_type", "name")]
        account_choices.insert(0, (None, ""))
        account_list = [
            "{account.account_type} - {account.name}".format(account=account)
            for account in Account.objects.filter(active=True).order_by("account_type", "name").select_related("account_type")
        ]

        self.fields["category"].widget = ListTextWidget(data_list=Category.objects.all().order_by("name"), name="category-list")
        self.fields["budget"].widget = ListTextWidget(data_list=Budget.objects.filter(active=True).order_by("name"), name="budget-list")
        self.fields["from_account"].widget = ListTextWidget(data_list=account_list, name="from_account_list")
        self.fields["to_account"].widget = ListTextWidget(data_list=account_list, name="to_account_list")
        self.fields["to_account"].choices = account_choices
        self.fields["amount"].initial = ["0", get_default_currency(user=user)]

        self.fields["transaction_type"].choices = [
            (k, v)
            for k, v in TransactionJournalEntry.TransactionType.choices
            if k != TransactionJournalEntry.TransactionType.START and k != TransactionJournalEntry.TransactionType.RECONCILIATION
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


class TransactionFilterForm(forms.Form):
    start_date = forms.DateField(widget=DateInput, required=False)
    end_date = forms.DateField(widget=DateInput, required=False)
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Search descriptions"}))
    account = forms.CharField(required=False)
    category = forms.CharField(required=False)
    budget = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(TransactionFilterForm, self).__init__(*args, **kwargs)

        self.fields["account"].widget = ListTextWidget(
            data_list=Account.objects.filter(active=True).order_by("name"), name="account-list", attrs={"placeholder": "Select account"}
        )
        self.fields["category"].widget = ListTextWidget(
            data_list=Category.objects.all().order_by("name"), name="category-list", attrs={"placeholder": "Select category"}
        )
        self.fields["budget"].widget = ListTextWidget(
            data_list=Budget.objects.filter(active=True).order_by("name"), name="budget-list", attrs={"placeholder": "Select budget"}
        )
