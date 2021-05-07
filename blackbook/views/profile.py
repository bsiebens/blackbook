from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render
from django.urls import reverse

from ..forms import UserProfileForm
from ..utilities import set_message, set_message_and_redirect
from ..models import get_default_value, get_default_currency


@login_required
def profile(request):
    initial_data = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "default_currency": get_default_currency(user=request.user),
        "default_period": get_default_value("default_period", default_value=None, user=request.user),
    }

    profile_form = UserProfileForm(initial=initial_data)
    password_form = PasswordChangeForm(user=request.user)

    if request.POST:
        if "profile_submit" in request.POST:
            profile_form = UserProfileForm(request.POST)

            if profile_form.is_valid():
                request.user.first_name = profile_form.cleaned_data["first_name"]
                request.user.last_name = profile_form.cleaned_data["last_name"]
                request.user.email = profile_form.cleaned_data["email"]
                request.user.username = profile_form.cleaned_data["email"]
                request.user.save()

                request.user.userprofile.default_currency = profile_form.cleaned_data["default_currency"]
                request.user.userprofile.default_period = profile_form.cleaned_data["default_period"]
                request.user.userprofile.save()

                return set_message_and_redirect(request, "s|Your profile has been updated succesfully!", reverse("blackbook:profile"))
            else:
                set_message(request, "f|Your profile could not be saved. Please correct the errors below and try again.")

        if "password_submit" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)

                return set_message_and_redirect(request, "s|Your password has been updated succesfully!", reverse("blackbook:profile"))
            else:
                set_message(request, "f|Your password could not be updated. Please correct the errors below and try again.")

    return render(request, "blackbook/profile.html", {"profile_form": profile_form, "password_form": password_form})