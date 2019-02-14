from django.apps import AppConfig


class PlaylistConfig(AppConfig):
    """Playlist app
    """

    name = "playlist"

    def ready(self):
        """Method called when app start
        """
        from playlist.date_stop import check_date_stop_on_app_ready

        check_date_stop_on_app_ready()
