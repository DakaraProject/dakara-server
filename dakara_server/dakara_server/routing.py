from channels.routing import ProtocolTypeRouter, URLRouter

from dakara_server.token_auth import TokenAuthMiddlewareStack
from playlist import routing


application = ProtocolTypeRouter({
    # HTTP is auto-detected
    'websocket': TokenAuthMiddlewareStack(
        URLRouter(routing.websocket_urlpatterns)
    )
})
