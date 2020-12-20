from django import forms

from .models import get_currency_choices, Budget, Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["name", "account_type", "active", "include_in_net_worth", "iban", "currency", "virtual_balance"]


class UserProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    default_currency = forms.ChoiceField(choices=get_currency_choices())
    default_period = forms.ChoiceField(choices=Budget.Period.choices)