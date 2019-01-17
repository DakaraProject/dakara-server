from django.contrib.auth import get_user_model

from internal.permissions import BasePermissionCustom


UserModel = get_user_model()


class IsLibraryManager(BasePermissionCustom):
    """Allow access if user is super user or library manager
    """

    def has_permission(self, request, view):
        # for super user
        if request.user.is_superuser:
            return True

        # for manager
        return request.user.has_library_permission_level(UserModel.MANAGER)


class IsLibraryUser(BasePermissionCustom):
    """Allow access if user is super user or library user
    """

    def has_permission(self, request, view):
        # for super user
        if request.user.is_superuser:
            return True

        # for user
        return request.user.has_library_permission_level(UserModel.USER)
