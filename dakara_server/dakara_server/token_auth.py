"""Token authorization middleware for Django Channels 2

From: https://gist.github.com/rluts/22e05ed8f53f97bdd02eafdf38f3d60a
"""
from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework.authtoken.models import Token


class TokenAuthMiddleware:
    """Token authorization middleware for Django Channels 2
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        if b"authorization" in headers:
            token_name, token_key = headers[b"authorization"].decode().split()
            if token_name == "Token":
                self.authenticate_with_token(scope, token_key)

        # very basic way to achieve authentication through token passed via URL
        # it is not the best secured way
        # TODO find a better solution
        elif "query_string" in scope and scope["query_string"]:
            query_string = parse_qs(scope["query_string"].decode())
            if "token" in query_string:
                self.authenticate_with_token(scope, query_string["token"][0])

        return self.inner(scope, receive, send)

    def authenticate_with_token(self, scope, token_key):
        try:
            token = Token.objects.get(key=token_key)
            scope["user"] = token.user
            close_old_connections()
        except Token.DoesNotExist:
            scope["user"] = AnonymousUser()


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
