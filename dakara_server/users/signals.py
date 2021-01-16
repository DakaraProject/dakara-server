from django.dispatch import receiver
from rest_registration.signals import user_registered

from users import emails


@receiver(user_registered, dispatch_uid="handle_user_registered")
def handle_user_registered(sender, **kwargs):
    user = kwargs.get("user")
    emails.send_notification_to_managers(user)