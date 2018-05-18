from rest_framework import permissions
from django.contrib.auth import get_user_model

from users.permissions import BasePermissionCustom


UserModel = get_user_model()


class IsLibraryManagerOrReadOnly(BasePermissionCustom):
    """Handle permissions for updating library

    Permission scheme:
        Superuser can do anything;
        Library manager can do anything;
        Authenticated can only display;
        Unauthenticated user cannot see anything.
    """

    def has_permission_custom(self, request, view):
        # for safe methods only
        if request.method in permissions.SAFE_METHODS:
            return True

        # for modification
        return request.user.has_library_permission_level(UserModel.MANAGER)
