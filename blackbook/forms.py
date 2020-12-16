from django import forms

from .models import get_currency_choices, Budget, Category


class ProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    currency = forms.ChoiceField(choices=get_currency_choices())
    period = forms.ChoiceField(choices=Budget.Period.choices)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]