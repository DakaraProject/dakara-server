from rest_framework import permissions


class BasePermissionCustom(permissions.BasePermission):
    """Restrict object permission to access permission

    The main problem of `BasePermission` is that the default value for
    `has_permission_object` is True. This leads to problem when one permission
    class, that redefines `has_permission_object`, is combined with another
    one, that does not, with the `or` operator: the resulting
    `has_permission_object` value is alway True.

    Returning the same value as `has_permission` is for now the least dirty way
    to avoid this problem.
    """

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsReadOnly(BasePermissionCustom):
    """Allow access if request is GET, OPTION...
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsPost(BasePermissionCustom):
    """Allow access if request is POST
    """

    def has_permission(self, request, view):
        return request.method == "POST"


class IsPut(BasePermissionCustom):
    """Allow access if request is PUT
    """

    def has_permission(self, request, view):
        return request.method == "PUT"


class IsPatch(BasePermissionCustom):
    """Allow access if request is PATCH
    """

    def has_permission(self, request, view):
        return request.method == "PATCH"


class IsDelete(BasePermissionCustom):
    """Allow access if request is DELETE
    """

    def has_permission(self, request, view):
        return request.method == "DELETE"
