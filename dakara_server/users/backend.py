from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework.exceptions import ValidationError

UserModel = get_user_model()


class DakaraModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        if email is not None:
            try:
                user = UserModel.objects.get(email__iexact=email)
            except UserModel.DoesNotExist:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a nonexistent user (#20760).
                UserModel().set_password(password)
                return None

            if not user.check_password(password) or not self.user_can_authenticate(
                user
            ):
                return None

        else:
            user = super().authenticate(request, username, password, **kwargs)

        if user is None:
            return None

        if user.is_superuser:
            return user

        if not user.validated_by_email:
            raise ValidationError(
                {"non_field_errors": ["This user email has not been validated"]}
            )

        if not user.validated_by_manager:
            raise ValidationError(
                {"non_field_errors": ["This user has not been validated by a manager"]}
            )

        return user
