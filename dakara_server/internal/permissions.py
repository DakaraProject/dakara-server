from rest_framework import permissions


class BasePermissionCustom(permissions.BasePermission):
    """Restrict object permission to access permission
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
