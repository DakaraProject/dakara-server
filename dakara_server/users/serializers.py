from rest_framework import serializers
from rest_registration.api.serializers import DefaultLoginSerializer
from rest_registration.settings import registration_settings
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class DakaraLoginSerializer(DefaultLoginSerializer):
    """Login users

    Overriden to have validation errors if a user has either their account not
    validated by a manager, or their email not validated.
    """

    def validate(self, data):
        # try to authenticate now to catch validation errors
        registration_settings.LOGIN_AUTHENTICATOR(data, serializer=self)

        return data


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


class UserSerializerCurrent(serializers.ModelSerializer):
    """View users for current user
    """

    class Meta:
        model = UserModel
        fields = (
            "id",
            "username",
            "email",
            "is_superuser",
            "validated_by_email",
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


class UserForManagerWithPasswordSerializer(serializers.ModelSerializer):
    """Users edition for managers if emails are disabled
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
