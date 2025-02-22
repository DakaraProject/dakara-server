from drf_spectacular.authentication import TokenScheme


class PlayerTokenScheme(TokenScheme):
    """Documentation scheme for Player authentication with a token."""

    target_class = "playlist.authentications.PlayerTokenAuthentication"
    name = "PlayerTokenAuthentication"
    priority = 1
