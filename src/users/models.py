from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.fields import CaseInsensitiveCharField, CaseInsensitiveEmailField


class DakaraUser(AbstractUser):
    """Custom user."""

    username = CaseInsensitiveCharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
    )

    email = CaseInsensitiveEmailField(_("email address"), unique=True)

    # permission levels per application
    USER = "u"
    MANAGER = "m"

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
    LEVELS_PLAYLIST = [(USER, "User"), (MANAGER, "Manager")]

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
