import os
from abc import ABC

from django.apps import AppConfig

from internal.version import check_version


class DakaraConfig(AppConfig, ABC):
    """Dakara generic app config.

    This class call the `ready_no_reload` method on startup, which is not
    called by the reloader, and the `ready_reload` method on startup and when
    the reloader starts.
    """

    def ready(self):
        """Method called when app start.

        When the server is run with the `runserver` command, two instances of
        the project are running and hence this method is called twice: one for
        the reloader and one for the actual development server. The reloader
        creates the environment variable `RUN_MAIN` with the value "true", so
        it can be distinguighed.

        See: https://stackoverflow.com/q/33814615
        See: django/utils/autoreload.py
        """
        # The code below can be executed by the reloader
        self.ready_reload()

        if os.environ.get("RUN_MAIN") == "true":
            return

        # The code bellow cannot be executed by the reloader
        self.ready_no_reload()

    def ready_reload(self):
        """Method called when app start and by reloader.

        This is a stub, that can be overriden
        """

    def ready_no_reload(self):
        """Method called when app start, but not called by reloader.

        This is a stub, that can be overriden
        """


class InternalConfig(DakaraConfig):
    """Internal app."""

    name = "internal"

    def ready_no_reload(self):
        """Method called when app starts."""
        # check the version of the server
        check_version()
