from rest_framework import permissions
from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response
from django.contrib.auth import get_user_model # If used custom user model
from library.views import LibraryPagination as UsersPagination
from . import serializers
from . import permissions as users_permissions

UserModel = get_user_model()


class CurrentUser(views.APIView):
    permission_classes = [
            permissions.IsAuthenticated
            ]

    def get(self, request):
        user = request.user
        serializer = serializers.UserSerializer(user)

        return Response(serializer.data)


class UserList(generics.ListCreateAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    serializer_class = serializers.UserSerializer
    pagination_class = UsersPagination
    permission_classes = [
            users_permissions.IsUsersManagerOrReadOnly
    ]


class UserView(generics.RetrieveUpdateDestroyAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
            users_permissions.IsUsersManagerOrReadOnly,
            users_permissions.IsNotSelfOrReadOnly
    ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return serializers.UserUpdateManagerSerializer

        return serializers.UserSerializer


class PasswordView(generics.UpdateAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    serializer_class = serializers.PasswordSerializer
    permission_classes = [
            users_permissions.IsSelf
            ]
