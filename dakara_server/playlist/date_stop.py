import logging
from datetime import datetime

from django.utils import timezone
from playlist.models import Karaoke


tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)


def clear_date_stop():
    """Clear stop date and disable can add to playlist
    """
    karaoke = Karaoke.get_object()
    if not karaoke.date_stop or karaoke.date_stop > datetime.now(tz):
        logger.error("Clear date stop was called when it should not")
        return

    karaoke.can_add_to_playlist = False
    karaoke.date_stop = None
    karaoke.save()
    logger.info("Date stop was cleared and can add to playlist was disabled")
