from django import forms

from .models import get_currency_choices, get_default_currency


class UserProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    default_currency = forms.ChoiceField(choices=get_currency_choices())