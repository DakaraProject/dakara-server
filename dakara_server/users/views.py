from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from library.views import LibraryPagination as UsersPagination
from . import serializers
from . import permissions


UserModel = get_user_model()


class CurrentUserView(views.APIView):
    """View of the current user
    """
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """Retrieve the user
        """
        user = request.user
        serializer = serializers.UserSerializer(user)

        return Response(serializer.data)


class UserListView(generics.ListCreateAPIView):
    """List and creation of users
    """
    model = UserModel
    queryset = UserModel.objects.all()
    serializer_class = serializers.UserSerializer
    pagination_class = UsersPagination
    permission_classes = [
        permissions.IsUsersManagerOrReadOnly
    ]


class UserView(generics.RetrieveUpdateDestroyAPIView):
    """Edition and view of a user
    """
    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
        permissions.IsUsersManagerOrReadOnly,
        permissions.IsNotSelfOrReadOnly
    ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return serializers.UserUpdateManagerSerializer

        return serializers.UserSerializer


class PasswordView(generics.UpdateAPIView):
    """Edition of a user password
    """
    model = UserModel
    queryset = UserModel.objects.all()
    serializer_class = serializers.PasswordSerializer
    permission_classes = [
        permissions.IsSelf
    ]
