from rest_framework import serializers
from rest_registration.utils.users import authenticate_by_login_and_password_or_none
from rest_registration.api.serializers import DefaultLoginSerializer
from django.contrib.auth import get_user_model, update_session_auth_hash

UserModel = get_user_model()


class DakaraLoginSerializer(DefaultLoginSerializer):
    """Login users
    """

    def validate(self, data):
        # store the user now
        # any ValidationError should be caught
        data["user"] = authenticate_by_login_and_password_or_none(
            data["login"], data["password"]
        )

        return data

    def get_authenticated_user(self):
        # return the stored user
        return self.validated_data["user"]


class UserForPublicSerializer(serializers.ModelSerializer):
    """Display public data only
    """

    class Meta:
        model = UserModel
        fields = ("id", "username")
        read_only_fields = ("username",)


class UserSerializer(serializers.ModelSerializer):
    """Creation and view
    """

    class Meta:
        model = UserModel
        fields = (
            "id",
            "username",
            "password",
            "is_superuser",
            "users_permission_level",
            "library_permission_level",
            "playlist_permission_level",
        )
        read_only_fields = (
            "is_superuser",
            "users_permission_level",
            "library_permission_level",
            "playlist_permission_level",
        )
        extra_kwargs = {"password": {"write_only": True}}


class PasswordSerializer(serializers.ModelSerializer):
    """Password edition

    Can edit:
        Password.

    For editing other user info, create another serializer.
    """

    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = UserModel
        fields = ("password", "old_password")
        extra_kwargs = {"password": {"write_only": True, "required": True}}

    def validate_old_password(self, value):
        """Check old password is correct
        """
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Wrong password")

    def update(self, instance, validated_data):
        """Update the password
        """
        password = None
        if "password" in validated_data:
            password = validated_data.pop("password")

        instance = super().update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()
            # keep current user logged in
            update_session_auth_hash(self.context["request"], instance)

        return instance


class UserForManagerSerializer(PasswordSerializer):
    """Users edition for managers

    Can edit:
        Apps permission levels,
        Password.
    """

    class Meta:
        model = UserModel
        fields = (
            "id",
            "username",
            "email",
            "password",
            "is_superuser",
            "users_permission_level",
            "library_permission_level",
            "playlist_permission_level",
            "validated_by_manager",
            "validated_by_email",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "is_superuser",
            "validated_by_email",
        )
        extra_kwargs = {"password": {"write_only": True}}
