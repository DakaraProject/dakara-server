import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.core.cache import cache
from django.db.utils import OperationalError

from playlist.models import Karaoke

KARAOKE_JOB_NAME = "karaoke_date_stop"

tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
scheduler.start()


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


def check_date_stop_on_app_ready():
    """Check if date stop has expired and clear or schedule job accordingly
    """
    try:
        karaoke = Karaoke.get_object()

    # if database does not exist when checking date stop, abort the function
    # this case occurs on startup before running tests
    except OperationalError:
        return

    if karaoke.date_stop is not None:
        if karaoke.date_stop < datetime.now(tz):
            # Date stop has already expired
            clear_date_stop()
            return

        # Re-schedule date stop clear if not scheduled yet
        # Since this method may be called several times at startup
        if cache.get(KARAOKE_JOB_NAME) is not None:
            return

        job = scheduler.add_job(clear_date_stop, "date", run_date=karaoke.date_stop)
        cache.set(KARAOKE_JOB_NAME, job.id)
        logger.debug("New date stop job was scheduled")
