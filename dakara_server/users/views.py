from rest_framework import permissions
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.contrib.auth import get_user_model # If used custom user model

from .serializers import UserSerializer, UserUpdateSerializer

UserModel = get_user_model()

class UserList(ListCreateAPIView):

    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
        permissions.AllowAny # Or anon users can't register
    ]
    serializer_class = UserSerializer


class UserView(RetrieveUpdateDestroyAPIView):
    model = UserModel
    queryset = UserModel.objects.all()
    permission_classes = [
        permissions.AllowAny # Or anon users can't register
    ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer

        return UserSerializer


