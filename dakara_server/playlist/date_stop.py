import logging
from datetime import datetime

from django.db.utils import OperationalError
from django.utils import timezone

from playlist.models import Karaoke

KARAOKE_JOB_NAME = "karaoke_date_stop"

tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)


def clear_date_stop():
    """Clear stop date and disable can add to playlist."""
    try:
        karaoke = Karaoke.objects.get_object()

    # if database does not exist when checking date stop, abort the function
    except OperationalError:
        return

    if not karaoke.date_stop or karaoke.date_stop > datetime.now(tz):
        return

    karaoke.can_add_to_playlist = False
    karaoke.date_stop = None
    karaoke.save()
    logger.info("Date stop was cleared and can add to playlist was disabled")
