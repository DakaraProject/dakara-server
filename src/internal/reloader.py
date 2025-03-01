import os


def is_reloader():
    """Detect if the current instance is a reloader.

    When the server is run with the `runserver` command, two instances of the
    project are running and hence this method is called twice: one for the
    reloader and one for the actual development server. The reloader creates
    the environment variable `RUN_MAIN` with the value "true", so it can be
    distinguighed.

    Returns:
        bool: True if the current instance is a reloader.

    See: https://stackoverflow.com/q/33814615
    See: django/utils/autoreload.py
    """
    return os.environ.get("RUN_MAIN") == "true"
