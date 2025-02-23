from threading import Event

from django.db.backends.signals import connection_created
from django.dispatch import receiver

from internal.reloader import is_reloader

connection_created_once = Event()


@receiver(connection_created)
def handle_connection_created(connection, **kwargs):
    """Perform playlist initialization operations as soon as the database is
    ready."""
    if not connection_created_once.is_set():
        connection_created_once.set()

        from playlist.date_stop import check_date_stop_on_app_ready
        from playlist.models import clean_channel_names

        clean_channel_names()

        if is_reloader():
            return

        # not called by the reloader
        check_date_stop_on_app_ready()
