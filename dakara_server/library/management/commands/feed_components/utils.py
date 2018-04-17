import os
from difflib import SequenceMatcher

from .subtitle_parser import PARSER_BY_EXTENSION


def file_is_valid(filename):
    """Check the file validity

    A valid file:
        - Is not a hidden file.
        - Has a non-blacklisted extension.

    Args:
        filename (str): name of the file.

    Returns:
        (bool) true if the file is valid.
    """
    return all((
        # media file
        os.path.splitext(filename)[1] not in (
            '.db'
        ),

        # not hidden file
        filename[0] != ".",
    ))


def file_is_subtitle(filename):
    """Check that the file is a subtitle

    Args:
        filename (str): name of the file.

    Returns:
        (bool) true if the file is a subtitle file.
    """
    return os.path.splitext(filename)[1] in list(PARSER_BY_EXTENSION.keys())


def is_similar(string1, string2):
    """Detect if string1 and strin2 are similar

    Returns:
        None if strings are not similar.
        A float between 0 and 1 representing similarity, bigger is more
        similar.
    """
    THRESHOLD = 0.8
    ratio = SequenceMatcher(None, string1, string2).ratio()

    if ratio >= THRESHOLD:
        return ratio

    return None
