import os
from abc import ABC, abstractmethod

from django.apps import AppConfig

from internal.version import check_version


class DakaraConfig(AppConfig, ABC):
    """Dakara generic config

    This class call the ready_no_reload method on startup,
    which is not called by the reloader
    """

    def ready(self):
        """Method called when app start
        """
        # When the server is run with the `runserver` command, two instances of
        # the project are running and hence this method is called twice: one
        # for the reloader and one for the actual development server. The
        # reloader creates the environment variable `RUN_MAIN` with the value
        # "true", so it can be distinguighed.
        # See answers of https://stackoverflow.com/q/33814615
        # See django/utils/autoreload.py
        if os.environ.get("RUN_MAIN") == "true":
            return

        # The code bellow cannot be executed by the reloader
        self.ready_no_reload()

    @abstractmethod
    def ready_no_reload(self):
        """Method called when app start, but not called by reloader

        This is a stub, that needs to be overriden
        """


class InternalConfig(DakaraConfig):
    """Internal app
    """

    name = "internal"

    def ready_no_reload(self):
        """Method called when app start
        """
        # check the version of the server
        check_version()
