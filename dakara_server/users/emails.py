import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import get_template

logger = logging.getLogger(__name__)

UserModel = get_user_model()


def get_managers_emails():
    """Get users managers and superusers email
    """
    return [
        user.email
        for user in UserModel.objects.filter(
            Q(validated_by_email=True)
            & (Q(users_permission_level=UserModel.MANAGER) | Q(is_superuser=True))
        )
    ]


def send_notification_to_managers(user):
    """Send a notification email to user managers that a new user registered
    """
    if not settings.EMAIL_ENABLED:
        return

    # get users manager and superuser email
    managers_emails = get_managers_emails()

    # check there are at least one manager
    if not managers_emails:
        logger.warning(
            "No managers to send message to when validating new account of %s", user
        )
        return

    # send the mail
    send_mail(
        "New user registered",
        get_notification_to_managers(user),
        settings.SENDER_EMAIL,
        managers_emails,
        fail_silently=False,
    )


def get_notification_to_managers(user):
    """Create notification message for managers

    Args:
        user (DakaraUser): User in the message.

    Returns:
        str: Notification message.
    """
    template = get_template("notification_to_managers.txt")
    return template.render(
        {"user": user, "url": settings.HOST_URLS["USER_EDIT_URL"].format(id=user.id)}
    )


def send_notification_to_user_validated(user):
    """Send a notification email to validated user
    """
    if not settings.EMAIL_ENABLED:
        return

    # send the mail
    send_mail(
        "Account validated",
        get_notification_to_user_validated(),
        settings.SENDER_EMAIL,
        [user.email],
        fail_silently=False,
    )


def get_notification_to_user_validated():
    """Create notification message to users that have been validated

    Returns:
        str: Notification message.
    """
    template = get_template("notification_to_user_validated.txt")
    return template.render({"url": settings.HOST_URLS["LOGIN_URL"]})
