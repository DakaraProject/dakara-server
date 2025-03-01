from django.contrib.auth import get_user_model

from internal.permissions import BasePermissionCustom

UserModel = get_user_model()


class IsLibraryManager(BasePermissionCustom):
    """Allow access if user is super user or library manager."""

    def has_permission(self, request, view):
        return request.user.is_superuser or getattr(
            request.user, "is_library_manager", False
        )


class IsLibraryUser(BasePermissionCustom):
    """Allow access if user is super user or library manager/user."""

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_superuser
            or getattr(user, "is_library_manager", False)
            or getattr(user, "is_library_user", False)
        )
