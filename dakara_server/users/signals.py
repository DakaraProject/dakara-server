from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_registration.settings import registration_settings
from rest_registration.signals import user_registered
from rest_registration.utils.verification_notifications import (
    send_register_verification_email_notification,
)

from users import emails

DakaraUser = get_user_model()


@receiver(user_registered, dispatch_uid="handle_user_registered")
def handle_user_registered(sender, **kwargs):
    """Manage to send notification to managers when a user is created."""
    user = kwargs.get("user")
    emails.send_notification_to_managers(user)


@receiver(post_save, sender=DakaraUser, dispatch_uid="handle_superuser_created")
def handle_superuser_created(sender, **kwargs):
    """Manage to send verification email to created superusers."""
    user = kwargs.get("instance")
    created = kwargs.get("created")

    if (
        registration_settings.REGISTER_VERIFICATION_ENABLED
        and created
        and user.is_superuser
    ):
        send_register_verification_email_notification(None, user)
