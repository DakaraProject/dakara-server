from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError

UserModel = get_user_model()


class DakaraModelBackend(ModelBackend):
    """Custom authentication backend for the project

    Authenticate user by username or by email. If authenticated, superuser can
    always log in, otherwise the user must have its email validated and its
    account validated by a manager.
    """

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False

        # the superuser can always log in
        if user.is_superuser:
            return True

        # the email address of the user must have been validated
        if settings.EMAIL_ENABLED and not user.validated_by_email:
            raise ValidationError("This user email has not been validated")

        # the accont of the user must have been validated by a manager
        if not user.validated_by_manager:
            raise ValidationError(
                "This user account has not been validated by a manager"
            )

        return True
