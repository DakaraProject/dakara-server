from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from django.contrib.auth import get_user_model

from internal.permissions import BasePermissionCustom
from library.models import Song
from playlist.models import PlaylistEntry, Karaoke


UserModel = get_user_model()


class IsPlaylistManager(BasePermissionCustom):
    """Allow access if the user is super user or playlist manager
    """

    def has_permission(self, request, view):
        # for super user
        if request.user.is_superuser:
            return True

        # for manager
        return request.user.has_playlist_permission_level(UserModel.MANAGER)


class IsPlaylistUser(BasePermissionCustom):
    """Allow access if the user is super user or playlist user
    """

    def has_permission(self, request, view):
        # for super user
        if request.user.is_superuser:
            return True

        # for user
        return request.user.has_playlist_permission_level(UserModel.USER)


class IsPlayer(BasePermissionCustom):
    """Allow access if the user is super user or player
    """

    def has_permission(self, request, view):
        # for super user
        if request.user.is_superuser:
            return True

        # for player
        return request.user.has_playlist_permission_level(UserModel.PLAYER)


class IsOwner(permissions.BasePermission):
    """Allow access if the user owns the object
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsPlayingEntryOwner(BasePermissionCustom):
    """Allow access if the user owns the playing playlist entry
    """

    def has_permission(self, request, view):
        # get the playing song
        playlist_entry = PlaylistEntry.get_playing()

        # disallow access if there is no playlist entry
        if playlist_entry is None:
            return False

        return playlist_entry.owner == request.user


class IsSongEnabled(BasePermissionCustom):
    """Allow access if the song has no disabled tag
    """

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


class KaraokeIsNotStoppedOrReadOnly(permissions.BasePermission):
    """Grant access to not safe views if the kara is not in stop mode
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        karaoke = Karaoke.get_object()
        return karaoke.status != Karaoke.STOP
