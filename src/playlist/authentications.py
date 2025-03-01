from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import TokenAuthentication

from playlist.models import PlayerToken


class PlayerTokenAuthentication(TokenAuthentication):
    """Check if the token of the request is a player token.

    The normal authentication mechanism tries to get a user from the token
    provided in the HTTP headers, but it does not recognizes player tokens, as
    these tokens are not related to normal users. Consequently, we have to re-process
    the token again. For the device, we chose to take into consideration the
    HTTP headers only.

    Just as a Django Request, a DRF Request object stores the token in the
    `Authorization` HTTP header.
    """

    model = PlayerToken

    def authenticate_credentials(self, key):
        # check the token is a player token
        try:
            player_token = self.model.objects.get(key=key)

        except self.model.DoesNotExist:
            return None

        return AnonymousUser(), player_token
