from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication

from playlist.models import PlayerToken


class PlayerTokenAuthentication(BaseAuthentication):
    """Check if the token of the request is a player token."""

    def authenticate(self, request):
        # check the request has a token
        try:
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
