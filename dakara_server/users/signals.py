import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.dispatch import receiver
from django.template.loader import get_template
from rest_registration.signals import user_registered

logger = logging.getLogger(__name__)

UserModel = get_user_model()


@receiver(user_registered, dispatch_uid="send_notification_to_managers")
def send_notification_to_managers(sender, **kwargs):
    """Send a notification email to user managers that a new user registered
    """
    user = kwargs.get("user")

    # get users manager and superuser email
    managers_emails = [
        user.email
        for user in UserModel.objects.filter(
            Q(users_permission_level=UserModel.MANAGER) | Q(is_superuser=True)
        )
    ]

    # check there are at least one manager
    if not managers_emails:
        logger.warning(
            "No managers to send message to when validating new account of %s", user
        )
        return

    # create message content
    template = get_template("notification_to_managers.txt")
    content = template.render(
        {"user": user, "url": settings.HOST_URLS["NOTIFICATION_TO_MANAGERS_URL"]}
    )

    # send the mail
    send_mail(
        "New user registered",
        content,
        settings.SENDER_EMAIL,
        managers_emails,
        fail_silently=False,
    )
