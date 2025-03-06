"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dakara_server.settings.development")

# Initialize Django ASGI application early to ensure the AppRegistry is
# populated before importing code that may import ORM models.
asgi_application = get_asgi_application()

from dakara_server.routing import websocket_urlpatterns  # noqa E402
from dakara_server.token_auth import TokenAuthMiddleware  # noqa E402

application = ProtocolTypeRouter(
    {
        "http": asgi_application,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(TokenAuthMiddleware(URLRouter(websocket_urlpatterns)))
        ),
    }
)
