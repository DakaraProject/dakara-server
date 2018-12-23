import re
from collections import OrderedDict
from abc import ABC, abstractmethod

import pysubs2


class SubtitleParser(ABC):
    """Abstract class for subtitle parser

    Args:
        filepath (str): path of the file to extract lyrics from.
    """

    @abstractmethod
    def __init__(self, filepath):
        pass

    @abstractmethod
    def get_lyrics(self):
        """Extract lyrics
        """
        return ""


class TXTSubtitleParser(SubtitleParser):
    """Subtitle parser for txt files
    """

    def __init__(self, filepath):
        with open(filepath) as file:
            self.content = file.read()

    def get_lyrics(self):
        return self.content


class Pysubs2SubtitleParser(SubtitleParser):
    """Subtitle parser for ass, ssa and srt files

    This parser extracts cleaned lyrics from the provided subtitle file.

    It uses the `pysubs2` package to parse the ASS file.

    Attributes:
        content (pysubs2 object): parsed subtitle.
        override_sequence (regex matcher): regex that matches any tag and any
            drawing area.
    """

    override_sequence = re.compile(
        r"""
                \{.*?\\p\d.*?\}     # look for drawing area start tag
                .*?                 # select draw instructions
                (?:                 # until...
                    \{.*?\\p0.*?\}  # draw area end tag
                    |
                    $               # or end of line
                )
                |
                \{.*?\}             # or simply select tags
            """,
        re.UNICODE | re.VERBOSE,
    )

    def __init__(self, filepath):
        self.content = pysubs2.load(filepath)

    def get_lyrics(self):
        """Gives the cleaned text of the Event block

        The text is cleaned in two ways:
            - All tags are removed;
            - Consecutive lines with the same content, the same start and end
                time are merged. This prevents from getting "extra effect
                lines" in the file.

        Returns:
            (str) Cleaned lyrics.
        """
        lyrics = []

        # previous line handles
        event_previous = None

        # loop over each dialog line
        for event in self.content:

            # Ignore comments
            if event.is_comment:
                continue

            # alter the cleaning regex
            event.OVERRIDE_SEQUENCE = self.override_sequence

            # clean the line
            line = event.plaintext.strip()

            # Ignore empty lines
            if not line:
                continue

            # append the cleaned line conditionnaly
            # Don't append if the line is a duplicate of previous line
            if not (
                event_previous
                and event_previous.plaintext.strip() == line
                and event_previous.start == event.start
                and event_previous.end == event.end
            ):

                lyrics.append(line)

            # update previous line handles
            event_previous = event

        return "\n".join(lyrics)


PARSER_BY_EXTENSION = OrderedDict(
    (
        (".ass", Pysubs2SubtitleParser),
        (".ssa", Pysubs2SubtitleParser),
        (".srt", Pysubs2SubtitleParser),
        (".txt", TXTSubtitleParser),
    )
)
