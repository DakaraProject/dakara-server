from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class SettingsView(APIView):
    """Settings of the Dakara server
    """

    permission_classes = (AllowAny,)

    def get(self, request):
        """Get application settings, version and date
        """
        data = {
            "version": settings.VERSION,
            "date": settings.DATE,
            "email_enabled": settings.EMAIL_ENABLED,
        }

        return Response(data, status.HTTP_200_OK)
