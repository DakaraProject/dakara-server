import logging

from django.conf import settings
from packaging.version import parse

logger = logging.getLogger("django")


def check_version():
    """Check the version of the server and display a warning if on non-release."""
    # log server version
    logger.info("Dakara server %s (%s)", settings.VERSION, settings.DATE)

    # check version is a release
    version = parse(settings.VERSION)
    if version.is_prerelease:
        logger.warning("You are running a dev version, use it at your own risks!")
