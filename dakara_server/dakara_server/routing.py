from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import playlist.routing
from dakara_server.token_auth import TokenAuthMiddlewareStack


application = ProtocolTypeRouter(
    {
        # HTTP is auto-detected
        "websocket": AllowedHostsOriginValidator(
            TokenAuthMiddlewareStack(URLRouter(playlist.routing.websocket_urlpatterns))
        )
    }
)
