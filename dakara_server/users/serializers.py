from rest_framework import serializers
from django.contrib.auth import get_user_model # If used custom user model
from django.contrib.auth.models import Group

UserModel = get_user_model()

class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'name',)

class UserSerializer(serializers.ModelSerializer):
    """ Serializer for creation and view
    """

    password = serializers.CharField(write_only=True)
    id = serializers.CharField(read_only=True)
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'password', 'groups')

    def create(self, validated_data):
        user_group = Group.objects.get(name="Playlist User")

        password = validated_data.pop('password')

        instance = super(UserSerializer, self).create(validated_data)
        instance.set_password(password)
        instance.save()
        instance.groups.add(user_group)

        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    """ Serializer for updating users

        Can edit:
            Password.
    """

    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserModel
        fields = ('password',)

    def update(self, instance, validated_data):
        password = None
        if 'password' in validated_data:
            password = validated_data.pop('password')

        instance = super(UserUpdateSerializer, self).update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()

        return instance


class UserUpdateManagerSerializer(UserUpdateSerializer):
    """ Serializer for updating users for managers

        Can edit:
            Group;
            Password.
    """

    class Meta:
        model = UserModel
        fields = ('password', 'groups')
