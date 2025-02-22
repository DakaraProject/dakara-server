from rest_framework import serializers


class SettingsSerializer(serializers.Serializer):
    """Settings."""

    version = serializers.CharField(read_only=True)
    date = serializers.DateTimeField(read_only=True)
    email_enabled = serializers.BooleanField(read_only=True)
