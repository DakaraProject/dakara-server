from rest_framework import permissions
from users.permissions import BasePermissionCustom

class IsPlaylistManagerOrOwnerOrReadOnly(BasePermissionCustom):
    """ Handle permissions to modify playlist entries

        Permission scheme:
            Superuser can edit anything;
            Playlist manager can edit anything;
            Authenticated user can only edit their own data and display anything;
            Unauthenticated user cannot see anything.
    """
    def has_object_permission(self, request, view, obj):
        # for safe methods only
        if request.method in permissions.SAFE_METHODS:
            return True

        # if the user is the superuser or the users manager, allow access
        if request.user.is_superuser:
            return True

        # for manager
        if request.user.has_playlist_permission_level('m'):
            return True

        # if the object belongs to the user
        return obj.owner == request.user

class IsPlaylistUserOrReadOnly(BasePermissionCustom):
    """ Handle permissions for creating playlist entries

        Permission scheme:
            Superuser can do anything;
            Playlist user can do anything;
            Authenticated can only display;
            Unauthenticated user cannot see anything.
    """
    def has_permission_custom(self, request, view):
        # for safe methods only
        if request.method in permissions.SAFE_METHODS:
            return True

        # for modification
        return request.user.has_playlist_permission_level('u')

class IsPlaylistManagerOrReadOnly(BasePermissionCustom):
    """ Handle permissions for changing player status

        Permission scheme:
            Superuser can do anything;
            Playlist manager can do anything;
            Authenticated can only display;
            Unauthenticated user cannot see anything.
    """
    def has_permission_custom(self, request, view):
        # for safe methods only
        if request.method in permissions.SAFE_METHODS:
            return True

        # for modification
        return request.user.has_playlist_permission_level('m')

class IsPlayer(BasePermissionCustom):
    """ Handle permissions player management

        Permission scheme:
            Superuser can do anything;
            Player can do anything;
            Authenticated cannot do anything;
            Unauthenticated user cannot see anything.
    """
    def has_permission_custom(self, request, view):
        return request.user.has_playlist_permission_level('p')
