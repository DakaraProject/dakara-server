from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication

from playlist.models import PlayerToken


class PlayerTokenAuthentication(BaseAuthentication):
    """Check if the token of the request is a player token."""

    def authenticate(self, request):
        # check the request has a token
        try:
            # NOTE: The normal authentication mechanism tries to get a user
            # from the token provided in the HTTP headers, but does not
            # recognizes player tokens, as this is not related to a normal
            # user. Consequently, we have to re-process the token again. For
            # the device, we chose to take into consideration the HTTP headers
            # only.

            # just as Django Request, DRF Request object stores the
            # Authorization HTTP header this way
            _, token = request.META["HTTP_AUTHORIZATION"].split()

        except (KeyError, ValueError):
            return None

        # check the token is a player token
        try:
            player_token = PlayerToken.objects.get(key=token)

        except PlayerToken.DoesNotExist:
            return None

        return AnonymousUser(), player_token

    def authenticate_header(self, request):
        # required as otherwise 401 responses are converted to 403 responses
        return "Invalid player token"
