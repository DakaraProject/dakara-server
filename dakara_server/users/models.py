from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class DakaraUserManager(UserManager):
    """Custom user manager to handle case insensitive usernames
    """

    def get_by_natural_key(self, username):
        """ Search a username case insensitively
        """
        return self.get(username__iexact=username)

    def _create_user(self, username, *args, **kwargs):
        """ Generic method to create new users

            Check if the username is free, otherwise raise a `ValueError`.
        """
        # check if username is free before creating user with this username
        if self.is_username_taken(username):
            raise ValueError("The username must be case insensitively unique")

        return super()._create_user(username, *args, **kwargs)

    def is_username_taken(self, username):
        """ Check if a similar username exists with the natural method

            Since we've set the search to be case insensitive, it will find it
            case insensitively.
        """
        try:
            if self.get_by_natural_key(username):
                return True

        except ObjectDoesNotExist:
            pass

        return False


class DakaraUser(AbstractUser):
    """Custom user
    """
    objects = DakaraUserManager()

    # permission levels per application
    LEVELS_GENERICS = [
        ("u", "User"),
        ("m", "Manager"),
    ]

    # role for Users app
    users_permission_level = models.CharField(
        max_length=1,
        choices=LEVELS_GENERICS,
        null=True,
    )

    # role for Libraryapp
    library_permission_level = models.CharField(
        max_length=1,
        choices=LEVELS_GENERICS,
        null=True,
    )

    # role for Playlist app
    LEVELS_PLAYLIST = [
        ("p", "Player"),
    ]

    LEVELS_PLAYLIST.extend(LEVELS_GENERICS)
    playlist_permission_level = models.CharField(
        max_length=1,
        choices=LEVELS_PLAYLIST,
        null=True,
    )

    def _has_permission_level(self, user_permission_level,
                              requested_permission_level):
        """ Check if the user has the requested app permission level
        """
        # the superuser can do anything
        if self.is_superuser:
            return True

        # the manager level includes everyone else level, except for the player
        if user_permission_level == 'm' and requested_permission_level != 'p':
            return True

        return user_permission_level == requested_permission_level

    def has_users_permission_level(self, permission_level):
        """ Check if the user has the requested users permission level
        """
        return self._has_permission_level(
            self.users_permission_level,
            permission_level
        )

    def has_library_permission_level(self, permission_level):
        """ Check if the user has the requested library permission level
        """
        return self._has_permission_level(
            self.library_permission_level,
            permission_level
        )

    def has_playlist_permission_level(self, permission_level):
        """ Check if the user has the requested playlist permission level
        """
        return self._has_permission_level(
            self.playlist_permission_level,
            permission_level
        )
