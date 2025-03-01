from internal.apps import DakaraConfig
from playlist import signals  # noqa F401


class PlaylistConfig(DakaraConfig):
    """Playlist app."""

    name = "playlist"
