from rest_framework import permissions
from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response
from django.contrib.auth import get_user_model # If used custom user model

from .serializers import (
        UserSerializer,
        UserUpdateSerializer,
        UserUpdateManagerSerializer,
        )
from .permissions import IsUsersManagerOrReadOnly, IsUsersManagerOrSelfOrReadOnly

UserModel = get_user_model()


class CurrentUser(views.APIView):
    permission_classes = [
            permissions.IsAuthenticated
            ]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)

        return Response(serializer.data)


class UserList(generics.ListCreateAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
            IsUsersManagerOrReadOnly
    ]


class UserView(generics.RetrieveUpdateDestroyAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
        IsUsersManagerOrSelfOrReadOnly
    ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            if self.request.user.has_users_permission_level('m'):
                return UserUpdateManagerSerializer

            return UserUpdateSerializer

        return UserSerializer
