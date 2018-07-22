import json


def parse_work(filepath):
    """Default parse module for work data file in JSON.

    Args:
        filepath : path of the file to parse (must be JSON).
    """

    with open(filepath) as f:
        return json.load(f)
