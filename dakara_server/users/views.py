from rest_framework import permissions
from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response
from django.contrib.auth import get_user_model # If used custom user model
from django.contrib.auth.models import Group

from .serializers import (
        UserSerializer,
        UserUpdateSerializer,
        UserUpdateManagerSerializer,
        GroupSerializer,
        )
from .permissions import IsUsersManagerOrReadOnly, IsUsersManagerOrSelfOrReadOnly

UserModel = get_user_model()


class CurrentUser(views.APIView):
    permission_classes = [
            permissions.IsAuthenticated
            ]

    def get(self, request):
        print(request.user)
        user = request.user
        serializer = UserSerializer(user)

        return Response(serializer.data)


class GroupList(generics.ListAPIView):
    model = Group
    queryset = Group.objects.all()
    permission_classes = [
            permissions.IsAuthenticated
            ]

    serializer_class = GroupSerializer


class UserList(generics.ListAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
        permissions.IsAuthenticated
    ]
    serializer_class = UserSerializer


class UserCreate(generics.CreateAPIView):
    model = UserModel
    permission_classes = [
                IsUsersManagerOrReadOnly
            ]

    serializer_class = UserSerializer


class UserView(generics.RetrieveUpdateDestroyAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
        IsUsersManagerOrSelfOrReadOnly
    ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer

        return UserSerializer

class UserManagerView(generics.UpdateAPIView, generics.DestroyAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
            IsUsersManagerOrReadOnly
            ]

    serializer_class = UserUpdateManagerSerializer
