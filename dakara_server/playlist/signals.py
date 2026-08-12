from threading import Event

from django.db.backends.signals import connection_created
from django.db.utils import ProgrammingError
from django.dispatch import receiver

connection_created_once = Event()


@receiver(connection_created)
def handle_connection_created(connection, **kwargs):
    """Perform playlist initialization operations as soon as the database is
    ready."""
    # make sure this code is called only once
    if not connection_created_once.is_set():
        connection_created_once.set()

        from playlist.models import clean_channel_names

        try:
            clean_channel_names()

        except ProgrammingError:
            # database not yet created
            pass
