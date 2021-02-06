from rest_framework import serializers
from rest_registration.utils.users import (
    authenticate_by_login_and_password_or_none,
    get_user_by_lookup_dict,
    get_user_login_field_names,
)
from rest_registration.api.serializers import (
    DefaultLoginSerializer,
    DefaultSendResetPasswordLinkSerializer,
)
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


class DakaraSendResetPasswordLinkSerializer(DefaultSendResetPasswordLinkSerializer):
    def get_user_or_none(self):
        return self.get_user_by_login_or_none(self.validated_data["login"])

    @staticmethod
    def get_user_by_login_or_none(login, require_verified=False):
        user = None
        for login_field_name in get_user_login_field_names():
            user = get_user_by_lookup_dict(
                {f"{login_field_name}__iexact": login},
                default=None,
                require_verified=require_verified,
            )
            if user:
                break

        return user


class UserForPublicSerializer(serializers.ModelSerializer):
    """Display public data only
    """

    class Meta:
        model = UserModel
        fields = ("id", "username")
        read_only_fields = ("username",)


class UserSerializer(serializers.ModelSerializer):
    """View users for non managers
    """

    class Meta:
        model = UserModel
        fields = (
            "id",
            "username",
            "is_superuser",
            "users_permission_level",
            "library_permission_level",
            "playlist_permission_level",
        )


class UserForManagerSerializer(serializers.ModelSerializer):
    """Users edition for managers
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


class UserCreationForManagerSerializer(serializers.ModelSerializer):
    """Users creation for managers
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
            "is_superuser",
            "validated_by_email",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "validated_by_manager": {"default": True},
        }

    def create(self, validated_data):
        """Create a user

        We shouldn't use the parent class method, as it will bypass the
        UserManager's secured user creation methods.
        """
        instance = UserModel.objects.create_user(**validated_data)
        instance.save()

        return instance
