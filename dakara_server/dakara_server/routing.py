from django.urls import re_path

from playlist import consumers


websocket_urlpatterns = [
    re_path(r"^ws/playlist/device/$", consumers.PlaylistDeviceConsumer.as_asgi())
]
