from rest_framework import permissions

class BasePermissionCustom(permissions.BasePermission):
    """ Base permission class for the project, check the basic permissions

        Permission scheme:
            Superuser can do anything;
            Unauthenticated user cannot do anything.

        The permission methods call a custom method for specific permissions.
    """

    def has_permission(self, request, view):

        # if the user is not authenticated, deny access
        if not request.user or not request.user.is_authenticated():
            return False

        # if the user is the superuser or the users manager, allow access
        if request.user.is_superuser:
            return True

        # call specific permission check
        return self.has_permission_custom(request, view)

    def has_permission_custom(self, request, view):
        """ Stub for specific permissions check
        """
        return True


def is_user_in_group(user, group_name):
    """ Check if the user is member of the provided group

        Should be moved into User class when available.
    """
    return user.groups.filter(name=group_name)


class IsUsersManagerOrReadOnly(BasePermissionCustom):
    """ Handle permissions for the User app

        Permission scheme:
            Superuser can edit anything;
            Users Manager can edit anything;
            Authenticated user can only display data;
            Unauthenticated user cannot see anything.
    """
    def has_permission_custom(self, request, view):
        # for manager
        if is_user_in_group(request.user, "User Manager"):
            return True

        # for safe methods only
        if request.method in permissions.SAFE_METHODS:
            return True


class IsUsersManagerOrSelfOrReadOnly(BasePermissionCustom):

    def has_object_permission(self, request, view, obj):
        # for safe methods only
        if request.method in permissions.SAFE_METHODS:
            return True

        # if the user is the superuser or the users manager, allow access
        if request.user.is_superuser:
            return True

        # for manager
        if is_user_in_group(request.user, "User Manager"):
            return True

        # if the object belongs to the user
        return obj == request.user
