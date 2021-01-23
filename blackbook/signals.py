from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_userprofile(sender, instance, created, **kwargs):
    try:
        instance.userprofile

    except get_user_model().userprofile.RelatedObjectDoesNotExist:
        UserProfile.objects.create(user=instance)