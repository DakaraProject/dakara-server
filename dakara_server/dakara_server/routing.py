from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from dakara_server.token_auth import TokenAuthMiddlewareStack
from playlist import routing


application = ProtocolTypeRouter({
    # HTTP is auto-detected
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        )
    )
})
