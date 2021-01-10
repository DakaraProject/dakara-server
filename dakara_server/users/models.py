from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _


class DakaraUserManager(UserManager):
    """Custom user manager to handle case insensitive usernames
    """

    def get_by_natural_key(self, username):
        """Search a username case insensitively
        """
        return self.get(username__iexact=username)


def username_different_case_validator(username):
    """Raise validation error if a user already exists with a different case

    If a user already exists with the same case, the unique constraint already
    raises an error.
    """
    try:
        user = DakaraUser.objects.get_by_natural_key(username)
        if user.username != username:
            raise ValidationError(_("A user with that username already exists."))

    except ObjectDoesNotExist:
        pass


def email_different_case_validator(email):
    """Raise validation error if a user already exists with a different case email
    """
    try:
        user = DakaraUser.objects.get(email__iexact=email)
        if user.email != email:
            raise ValidationError("user with this email address already exists.")

    except ObjectDoesNotExist:
        pass


class DakaraUser(AbstractUser):
    """Custom user
    """

    objects = DakaraUserManager()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[AbstractUser.username_validator, username_different_case_validator],
        error_messages={"unique": _("A user with that username already exists.")},
    )

    email = models.EmailField(
        _("email address"), unique=True, validators=[email_different_case_validator]
    )

    # permission levels per application
    USER = "u"
    MANAGER = "m"
    PLAYER = "p"

    # role for Users app
    LEVELS_USERS = [(USER, "User"), (MANAGER, "Manager")]

    users_permission_level = models.CharField(
        max_length=1, choices=LEVELS_USERS, null=True
    )

    # role for Libraryapp
    LEVELS_LIBRARY = [(USER, "User"), (MANAGER, "Manager")]
    library_permission_level = models.CharField(
        max_length=1, choices=LEVELS_LIBRARY, null=True
    )

    # role for Playlist app
    LEVELS_PLAYLIST = [(PLAYER, "Player"), (USER, "User"), (MANAGER, "Manager")]

    playlist_permission_level = models.CharField(
        max_length=1, choices=LEVELS_PLAYLIST, null=True, default=USER
    )

    validated_by_email = models.BooleanField(default=False)

    validated_by_manager = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def is_users_user(self):
        return self.users_permission_level == self.USER

    @property
    def is_users_manager(self):
        return self.users_permission_level == self.MANAGER

    @property
    def is_library_user(self):
        return self.library_permission_level == self.USER

    @property
    def is_library_manager(self):
        return self.library_permission_level == self.MANAGER

    @property
    def is_playlist_user(self):
        return self.playlist_permission_level == self.USER

    @property
    def is_playlist_manager(self):
        return self.playlist_permission_level == self.MANAGER

    @property
    def is_player(self):
        return self.playlist_permission_level == self.PLAYER


class UserExistsWithDifferentCaseError(ValueError):
    """Error raised when creating a user with just a different of case
    """
