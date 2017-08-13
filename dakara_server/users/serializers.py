from rest_framework import serializers
from django.contrib.auth import (
        get_user_model, # If used custom user model
        update_session_auth_hash,
        )
from .models import DakaraUser


UserModel = get_user_model()


class PermissionLevelField(serializers.ChoiceField):
    """ Apps permission level field

        It does the dirty job in one place.
    """
    def __init__(self, target, *args, **kwargs):
        super(PermissionLevelField, self).__init__(
                *args,
                choices=DakaraUser._meta.get_field(target).choices,
                **kwargs
                )


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for creation and view
    """

    password = serializers.CharField(write_only=True)
    id = serializers.CharField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    users_permission_level = PermissionLevelField(
            target="users_permission_level",
            read_only=True
            )

    library_permission_level = PermissionLevelField(
            target="library_permission_level",
            read_only=True
            )

    playlist_permission_level = PermissionLevelField(
            target="playlist_permission_level",
            read_only=True
            )

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'password',
                'is_superuser',
                'users_permission_level',
                'library_permission_level',
                'playlist_permission_level')

    def create(self, validated_data):
        password = validated_data.pop('password')
        instance = super(UserSerializer, self).create(validated_data)
        instance.set_password(password)
        instance.playlist_permission_level = 'u'
        instance.save()

        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    """ Serializer for updating users
        Only for password edit
        for editing other user info, create a new serializer

        Can edit:
            Password.
    """

    password = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = UserModel
        fields = ('password', 'old_password')

    def validate_old_password(self, value):
        # check old password is correct
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Wrong password")

    def update(self, instance, validated_data):
        password = None
        if 'password' in validated_data:
            password = validated_data.pop('password')

        instance = super(UserUpdateSerializer, self).update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()
            # keep current user logged in
            update_session_auth_hash(self.context['request'], instance)

        return instance


class UserUpdateManagerSerializer(UserUpdateSerializer):
    """ Serializer for updating users for managers

        Can edit:
            Apps permission levels,
            Password.
    """

    class Meta:
        model = UserModel
        fields = ('password',
                'users_permission_level',
                'library_permission_level',
                'playlist_permission_level')