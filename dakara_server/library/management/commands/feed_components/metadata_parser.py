import os
import subprocess
import json
from datetime import timedelta
from pymediainfo import MediaInfo

class MetadataParser:
    """ Base class for metadata parser

        The class works as an interface for the various metadata parsers
        available.

        This class itself is a null parser that always returns a timedelta 0
        duration.
    """
    def __init__(self, metadata):
        self.metadata = metadata

    @staticmethod
    def is_available():
        """ Check if the parser is callable
        """
        return True

    @classmethod
    def parse(cls, filename):
        """ Parse metadata from file name

            Args:
                filename (str): path of the file to parse.
        """
        return cls(None)

    @property
    def duration(self):
        """ Get duration as timedelta object

            Returns timedelta 0 if unable to get duration.
        """
        return timedelta(0)


class MediainfoMetadataParser(MetadataParser):
    """ Metadata parser based on PyMediaInfo (wrapper for MediaInfo)

        The class works as an interface for the MediaInfo class, provided by the
        pymediainfo module.

        It does not seem to work on Windows, as the mediainfo DLL cannot be
        found.
    """
    @staticmethod
    def is_available():
        """ Check if the parser is callable
        """
        return MediaInfo.can_parse()

    @classmethod
    def parse(cls, filename):
        """ Parse metadata from file name

            Args:
                filename (str): path of the file to parse.
        """
        metadata = MediaInfo.parse(filename)
        return cls(metadata)

    @property
    def duration(self):
        """ Get duration as timedelta object

            Returns timedelta 0 if unable to get duration.
        """
        general_track = self.metadata.tracks[0]
        duration = getattr(general_track, 'duration', 0) or 0
        return timedelta(milliseconds=int(duration))


class FFProbeMetadataParser(MetadataParser):
    """ Metadata parser based on ffprobe

        The class works as a wrapper for the `ffprobe` command. The ffprobe3
        module does not work, so we do our own here.

        The command is invoked through `subprocess`, so it should work on
        Windows as long as ffmpeg is installed and callable from the command
        line. Data are passed as JSON string.

        Freely inspired from [this proposed
        wrapper](https://stackoverflow.com/a/36743499) and the [code of
        ffprobe3](https://github.com/DheerendraRathor/ffprobe3/blob/master/ffprobe3/ffprobe.py).
    """
    @staticmethod
    def is_available():
        """ Check if the parser is callable
        """
        try:
            with open(os.devnull, 'w') as tempf:
                subprocess.check_call(
                        ["ffprobe", "-h"],
                        stdout=tempf,
                        stderr=tempf
                        )

                return True

        except:
            return False

    @classmethod
    def parse(cls, filename):
        """ Parse metadata from file name

            Args:
                filename (str): path of the file to parse.
        """
        command = ["ffprobe",
                "-loglevel",  "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                filename
                ]

        pipe = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
                )

        out, err = pipe.communicate()
        return cls(json.loads(out.decode(sys.stdout.encoding)))

    @property
    def duration(self):
        """ Get duration as timedelta object

            Returns timedelta 0 if unable to get duration.
        """
        # try in generic location
        if 'format' in self.metadata:
            if 'duration' in self.metadata['format']:
                return timedelta(seconds=float(
                    self.metadata['format']['duration']
                    ))

        # try in the streams
        if 'streams' in self.metadata:
            # commonly stream 0 is the video
            for s in self.metadata['streams']:
                if 'duration' in s:
                    return timedelta(seconds=float(s['duration']))

        # if nothing is found
        return timedelta(0)
