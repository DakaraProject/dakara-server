import os
import json


class JSONFileNotFound(Exception):
    """Raised when the JSON file at the path specified is not found."""


def parse_work(filepath):
    """Default parse module for work data file in JSON.

    Args:
        filepath : path of the file to parse (must be JSON).
    """

    if not os.path.isfile(filepath):
        raise JSONFileNotFound("JSON file at path '{}' not found.".format(filepath))

    with open(filepath) as f:
        return json.load(f)
