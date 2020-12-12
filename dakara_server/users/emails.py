import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import get_template

logger = logging.getLogger(__name__)

UserModel = get_user_model()


def get_managers_emails():
    """Get users manager and superuser email
    """
    return [
        user.email
        for user in UserModel.objects.filter(
            Q(users_permission_level=UserModel.MANAGER) | Q(is_superuser=True)
        )
    ]


def send_notification_to_managers(user):
    """Send a notification email to user managers that a new user registered
    """
    # get users manager and superuser email
    managers_emails = get_managers_emails()

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


def send_notification_to_user_validated(user):
    """Send a notification email to validated user
    """
    # create message content
    template = get_template("notification_to_user_validated.txt")
    content = template.render({"url": settings.HOST_URLS["LOGIN_URL"]})

    # send the mail
    send_mail(
        "Account validated",
        content,
        settings.SENDER_EMAIL,
        [user.email],
        fail_silently=False,
    )
