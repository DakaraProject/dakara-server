import os
import logging

from django.apps import AppConfig
from django.conf import settings


logger = logging.getLogger("django")


class DakaraConfig(AppConfig):
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

    def ready_no_reload(self):
        """Method called when app start, but not called by reloader

        This is a stub, that needs to be overriden
        """
        raise NotImplementedError()


class InternalConfig(DakaraConfig):
    """Internal app
    """

    name = "internal"

    def ready_no_reload(self):
        """Method called when app start
        """
        # log server version
        logger.info("Dakara server {} ({})".format(settings.VERSION, settings.DATE))
