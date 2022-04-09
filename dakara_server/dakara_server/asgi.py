"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from dakara_server.routing import websocket_urlpatterns
from dakara_server.token_auth import TokenAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dakara_server.settings.development")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(TokenAuthMiddleware(URLRouter(websocket_urlpatterns)))
        ),
    }
)
