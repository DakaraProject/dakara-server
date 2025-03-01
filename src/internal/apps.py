from abc import ABC

from django.apps import AppConfig

from internal.reloader import is_reloader
from internal.version import check_version


class DakaraConfig(AppConfig, ABC):
    """Dakara generic app config.

    This class call the `ready_no_reload` method on startup, which is not
    called by the reloader, and the `ready_reload` method on startup and when
    the reloader starts.
    """

    def ready(self):
        """Method called when app start."""
        # The code below can be executed by the reloader
        self.ready_reload()

        if is_reloader():
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
