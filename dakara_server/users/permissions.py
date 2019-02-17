from django.contrib.auth import get_user_model

from internal.permissions import BasePermissionCustom


UserModel = get_user_model()


class DummyRequest:
    """Convert a request dictionary to a request object
    """

    def __init__(self, **entries):
        self.__dict__.update(entries)


class IsUsersManager(BasePermissionCustom):
    """Allow access if user is super user or user manager
    """

    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.is_users_manager


class IsSelf(BasePermissionCustom):
    """Allow access if user if the object
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsNotSelf(IsSelf):
    """Allow access if user is not the object
    """

    def has_object_permission(self, request, view, obj):
        return not super().has_object_permission(request, view, obj)
