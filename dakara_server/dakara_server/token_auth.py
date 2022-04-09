"""Token authorization middleware for Django Channels 2.

From: https://gist.github.com/rluts/22e05ed8f53f97bdd02eafdf38f3d60a
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user

    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """Token authorization middleware for Django Channels 2."""

    async def __call__(self, scope, receive, send):
        # get token from headers
        headers = dict(scope["headers"])
        if b"authorization" in headers:
            token_name, token_key = headers[b"authorization"].decode().split()
            if token_name == "Token":
                await self.authenticate_with_token(scope, token_key)

        # get token from query string
        elif "query_string" in scope and scope["query_string"]:
            query_string = parse_qs(scope["query_string"].decode())
            if "token" in query_string:
                await self.authenticate_with_token(scope, query_string["token"][0])

        return await super().__call__(scope, receive, send)

    async def authenticate_with_token(self, scope, token_key):
        scope["user"] = AnonymousUser() if not token_key else await get_user(token_key)
        close_old_connections()
