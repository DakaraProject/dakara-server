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

    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        if email is not None:
            # try to authenticate by email first (case insensitively)
            # code inspired from django.contrib.auth.backends.ModelBackend.authenticate
            try:
                user = UserModel.objects.get(email__iexact=email)

            except UserModel.DoesNotExist:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a nonexistent user (#20760).
                UserModel().set_password(password)
                return None

            if not (user.check_password(password) and self.user_can_authenticate(user)):
                return None

        else:
            # otherwise authenticate using default process (i.e. using username)
            user = super().authenticate(request, username, password, **kwargs)

        # do not perform extra checks if the user cannot be logged in
        if user is None:
            return None

        # the superuser can always log in
        if user.is_superuser:
            return user

        # the email address of the user must have been validated
        if not user.validated_by_email:
            raise ValidationError("This user email has not been validated")

        # the accont of the user must have been validated by a manager
        if not user.validated_by_manager:
            raise ValidationError(
                "This user account has not been validated by a manager"
            )

        return user
