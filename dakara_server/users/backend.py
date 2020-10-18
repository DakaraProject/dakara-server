from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError


class DakaraModelBackend(ModelBackend):
    def authenticate(self, request, *args, **kwargs):
        user = super().authenticate(request, *args, **kwargs)

        if user is None:
            return None

        if user.is_superuser:
            return user

        if not user.validated_by_email:
            raise ValidationError("This user email has not been validated")

        if not user.validated_by_manager:
            raise ValidationError("This user has not been validated by a manager")

        return user
