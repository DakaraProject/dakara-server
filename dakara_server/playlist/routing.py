from django.conf.urls import url

from playlist import consumers


websocket_urlpatterns = [
    url(r"^ws/playlist/device/$", consumers.PlaylistDeviceConsumer)
]
