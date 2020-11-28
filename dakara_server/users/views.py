from django.contrib.auth import get_user_model
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_registration.settings import registration_settings
from rest_registration.utils.verification_notifications import (
    send_register_verification_email_notification,
)

from internal import permissions as internal_permissions
from users import permissions, serializers


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
        # serializer depends on permission level
        if permissions.IsUsersManager().has_permission(self.request, self):
            return serializers.UserCreationForManagerSerializer

        return serializers.UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        # send verification email if requested
        if registration_settings.REGISTER_VERIFICATION_ENABLED:
            send_register_verification_email_notification(self.request, user)


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
        # serializer depends on permission level
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
