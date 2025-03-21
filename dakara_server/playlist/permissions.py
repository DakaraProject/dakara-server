from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions

from internal.permissions import BasePermissionCustom
from library.models import Song
from playlist.models import Karaoke, PlayerToken, PlaylistEntry

UserModel = get_user_model()


class IsPlaylistManager(BasePermissionCustom):
    """Allow access if the user is super user or playlist manager."""

    def has_permission(self, request, view):
        return request.user.is_superuser or getattr(
            request.user, "is_playlist_manager", False
        )


class IsPlaylistUser(BasePermissionCustom):
    """Allow access if the user is super user or playlist manager/user."""

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_superuser
            or getattr(user, "is_playlist_manager", False)
            or getattr(user, "is_playlist_user", False)
        )


class IsPlayer(BasePermissionCustom):
    """Allow access if the user is super user or player."""

    def has_permission(self, request, view):
        # super user has all rights
        if request.user.is_superuser:
            return True

        # authentication must be made with a player token
        if not isinstance(request.auth, PlayerToken):
            return False

        karaoke = Karaoke.objects.get_object()

        # this verification is overkill as for now only one karaoke can exist
        return karaoke == request.auth.karaoke


class IsOwner(permissions.BasePermission):
    """Allow access if the user owns the object."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsPlayingEntryOwner(BasePermissionCustom):
    """Allow access if the user owns the playing playlist entry."""

    def has_permission(self, request, view):
        # get the playing song
        playlist_entry = PlaylistEntry.objects.get_playing()

        # disallow access if there is no playlist entry
        if playlist_entry is None:
            return False

        return playlist_entry.owner == request.user


class IsSongEnabled(BasePermissionCustom):
    """Allow access if the song has no disabled tag."""

    def has_permission(self, request, view):
        # get song
        song_id = request.data.get("song_id")
        if not song_id:
            return True

        # check the song has no disabled tags
        try:
            song = Song.objects.get(pk=song_id)
            return not any([t.disabled for t in song.tags.all()])

        except ObjectDoesNotExist:
            return True
