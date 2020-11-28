from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from internal import permissions as internal_permissions
from users import serializers
from users import permissions


UserModel = get_user_model()


class CurrentUserView(views.APIView):
    """View of the current user
    """

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer

    def get(self, request):
        """Retrieve the user
        """
        user = request.user
        serializer = self.serializer_class(user)

        return Response(serializer.data)


class UserListView(generics.ListCreateAPIView):
    """List and creation of users
    """

    model = UserModel
    queryset = UserModel.objects.all().order_by("username")
    permission_classes = [
        IsAuthenticated,
        permissions.IsUsersManager | internal_permissions.IsReadOnly,
    ]

    def get_serializer_class(self):
        if permissions.IsUsersManager().has_permission(self.request, self):
            return serializers.UserCreationForManagerSerializer

        return serializers.UserSerializer


class UserView(generics.RetrieveUpdateDestroyAPIView):
    """Edition and view of a user
    """

    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
        IsAuthenticated,
        permissions.IsUsersManager & permissions.IsNotSelf
        | internal_permissions.IsReadOnly,
    ]

    def get_serializer_class(self):
        if permissions.IsUsersManager().has_permission(self.request, self):
            return serializers.UserForManagerSerializer

        return serializers.UserSerializer


class PasswordView(generics.UpdateAPIView):
    """Edition of a user password
    """

    model = UserModel
    queryset = UserModel.objects.all()
    serializer_class = serializers.PasswordSerializer
    permission_classes = [IsAuthenticated, permissions.IsSelf]
