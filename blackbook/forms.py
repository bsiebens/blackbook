from django import forms
from django.utils import timezone, safestring

from djmoney.forms.fields import MoneyField
from djmoney.forms.widgets import MoneyWidget

from .models import get_currency_choices, get_default_currency, Account, TransactionJournal
from .utilities import validate_iban, format_iban


class DateInput(forms.DateInput):
    input_type = "date"


class BulmaMoneyWidget(MoneyWidget):
    template_name = "blackbook/forms/bulmamoneywidget.html"


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


class UserProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    default_currency = forms.ChoiceField(choices=get_currency_choices())


class AccountForm(forms.ModelForm):
    starting_balance = forms.DecimalField(max_digits=15, decimal_places=2, required=False, initial=0.0)

    class Meta:
        model = Account
        fields = ["name", "type", "active", "net_worth", "dashboard", "currency", "virtual_balance", "iban"]


class TransactionForm(forms.Form):
    short_description = forms.CharField()
    description = forms.CharField(required=False, widget=forms.Textarea)
    date = forms.DateField(initial=timezone.now, widget=DateInput)
    type = forms.ChoiceField(initial=TransactionJournal.TransactionType.WITHDRAWAL)
    amount = MoneyField(widget=BulmaMoneyWidget)
    source_account = forms.CharField(required=False)
    destination_account = forms.CharField(required=False)
    add_new = forms.BooleanField(required=False, initial=False, help_text="After saving, display this form again to add a new transaction.")
    display = forms.BooleanField(required=False, initial=True, help_text="After saving, display this form again to review this transaction.")

    def __init__(self, user, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)

        accounts = Account.objects.filter(active=True).order_by("type", "name")

        account_list = ["{type} - {account.name}".format(type=account.get_type_display(), account=account) for account in accounts]

        self.fields["source_account"].widget = ListTextWidget(data_list=account_list, name="source_account_list")
        self.fields["destination_account"].widget = ListTextWidget(data_list=account_list, name="destination_account_list")
        self.fields["amount"].inital = ["0", get_default_currency(user=user)]

        self.fields["type"].choices = [
            (k, v)
            for k, v in TransactionJournal.TransactionType.choices
            if k != TransactionJournal.TransactionType.START and k != TransactionJournal.TransactionType.RECONCILIATION
        ]

    def clean(self):
        cleaned_data = super().clean()

        transaction_type = cleaned_data.get("type")

        if transaction_type in [
            TransactionJournal.TransactionType.START,
            TransactionJournal.TransactionType.DEPOSIT,
            TransactionJournal.TransactionType.RECONCILIATION,
        ]:
            if cleaned_data.get("destination_account") == "":
                self.add_error("type", "Destination account must be set for this transaction type.")
                self.add_error("destination_account", "Destination account must be set for this transaction type.")

        elif transaction_type == TransactionJournal.TransactionType.WITHDRAWAL:
            if cleaned_data.get("source_account") == "":
                self.add_error("type", "Source account must be set for this transaction type.")
                self.add_error("source_account", "Source account must be set for this transaction type.")

        else:
            if cleaned_data.get("source_account") == "" or cleaned_data.get("destination_account") == "":
                self.add_error("type", "Source and destination account must be set for this transaction type.")

                if cleaned_data.get("source_account") == "":
                    self.add_error("source_account", "Source account must be set for this transaction type.")

                if cleaned_data.get("destination_account") == "":
                    self.add_error("destination_account", "Destination account must be set for this transaction type.")
