"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

import django
from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from dakara_server.routing import websocket_urlpatterns
from dakara_server.token_auth import TokenAuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dakara_server.settings.development")

django.setup()

application = ProtocolTypeRouter(
    {
        "http": AsgiHandler(),
        "websocket": AllowedHostsOriginValidator(
            TokenAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
