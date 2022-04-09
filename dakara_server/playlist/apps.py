from internal.apps import DakaraConfig


class PlaylistConfig(DakaraConfig):
    """Playlist app."""

    name = "playlist"

    def ready_no_reload(self):
        """Method called when app starts."""
        from playlist.date_stop import check_date_stop_on_app_ready

        check_date_stop_on_app_ready()

    def ready_reload(self):
        """Method called when app starts or restarts."""
        from playlist.models import clean_channel_names

        clean_channel_names()
