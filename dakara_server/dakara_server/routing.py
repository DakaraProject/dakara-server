from django.urls import re_path

from internal import consumers as internal_consumers
from playlist import consumers as playlist_consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/playlist/device/$", playlist_consumers.PlaylistDeviceConsumer.as_asgi()
    ),
    re_path(r"^ws/heartbeat/$", internal_consumers.HeartbeatConsumer.as_asgi()),
]
