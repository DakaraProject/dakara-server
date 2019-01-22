from django.contrib.auth import get_user_model

from internal.permissions import BasePermissionCustom


UserModel = get_user_model()


class IsLibraryManager(BasePermissionCustom):
    """Allow access if user is super user or library manager
    """

    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.is_library_manager


class IsLibraryUser(BasePermissionCustom):
    """Allow access if user is super user or library user
    """

    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.is_library_user
