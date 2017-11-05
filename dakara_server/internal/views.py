from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


##
# Version view
#


class VersionView(APIView):
    """ Class for user to get the player status
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        """ Get application version number
        """
        data = {
                'version': settings.VERSION,
                'date': settings.DATE
                }

        return Response(
                data,
                status.HTTP_200_OK
                )
