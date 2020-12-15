from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from datetime import timedelta
from guardian.shortcuts import assign_perm

from .models import UserProfile, Budget, BudgetPeriod, Account, Category, TransactionJournalEntry
from .utilities import calculate_period


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_userprofile(sender, instance, created, **kwargs):
    # Check to see if a user has a userprofile, if not create it.
    try:
        instance.userprofile

    except get_user_model().userprofile.RelatedObjectDoesNotExist:
        userprofile = UserProfile.objects.create(user=instance)


@receiver(post_save, sender=Budget)
def create_budget_period(sender, instance, created, **kwargs):
    if instance.auto_budget != Budget.AutoBudget.NO:
        current_date = timezone.now().date()
        period = calculate_period(periodicity=instance.auto_budget_period, start_date=current_date)

        if created:
            instance.periods.create(start_date=period["start_date"], end_date=period["end_date"], amount=instance.amount)

        else:
            current_period = instance.current_period

            if current_period is not None:
                if current_period.start_date == period["start_date"] and current_period.end_date == period["end_date"]:
                    if instance.tracker.has_changed("amount"):
                        current_period.amount = instance.amount
                        current_period.save(update_fields=["amount"])

                else:
                    current_period.end_date = current_date - timedelta(days=1)
                    current_period.save()

            if instance.current_period is None:
                instance.periods.create(start_date=period["start_date"], end_date=period["end_date"], amount=instance.amount)