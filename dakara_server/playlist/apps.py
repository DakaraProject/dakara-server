import os

from django.apps import AppConfig


class PlaylistConfig(AppConfig):
    """Playlist app
    """

    name = "playlist"

    def ready(self):
        """Method called when app start
        """
        # When the server is run with the `runserver` command, two instances of
        # the project are running and hence this method is called twice: one
        # for the reloader and one for the actual development server. The
        # reloader creates the environment variable `RUN_MAIN`, so it can be
        # distinguighed.
        # See answers of https://stackoverflow.com/q/33814615
        # See django/utils/autoreload.py
        if "RUN_MAIN" in os.environ:
            return

        # The code bellow cannot be executed by the reloader
        from playlist.date_stop import check_date_stop_on_app_ready

        check_date_stop_on_app_ready()
