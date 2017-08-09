#!/usr/bin/env python3
##
# Dakara Project
#
# Script for feeding the server database with songs from a directory
#

import os
import sys
import logging
import importlib
import progressbar
import warnings
import argparse
import subprocess
import json
from pymediainfo import MediaInfo
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from library.models import *
from library.serializers import SongSerializer
from django.test.client import RequestFactory

# get logger
logger = logging.getLogger(__file__)

# wrap a special stream for warnings
# the wrapping done by progressbar seems to reassign the ouput and flush it when
# needed, and not automatically
# if the standard error is wrapped, it mutes any exception, which is not
# acceptable
# so, we create a custom wrapped stream and assign warnings to use it
# since we cannot specify a new stream, we use stderr for that, and reassign
# it to its origineal value right after
original_stderr = sys.stderr
wrapped_stderr = progressbar.streams.wrap_stderr()
sys.stderr = original_stderr

# define a less verbose custom warnings formatting
def custom_formatwarning(message, *args, **kwargs):
    return "Warning: {}\n".format(message)

# assign warnings to write in the wrapped stream
def custom_showwarning(*args, **kwargs):
    wrapped_stderr.write(custom_formatwarning(*args, **kwargs))

# patch warnings output
warnings.formatwarning = custom_formatwarning
warnings.showwarning = custom_showwarning

# get file system encoding
file_coding = sys.getfilesystemencoding()


class DatabaseFeeder:
    """ Class representing a list of DatabaseFeederEntry to feed the database
        with
    """

    def __init__(
            self,
            listing,
            prefix="",
            dry_run=False,
            directory_path="",
            progress_show=False,
            no_add_on_error=False,
            custom_parser=None,
            metadata_parser='ffprobe',
            stdout=sys.stdout,
            stderr=sys.stderr
            ):
        """ Constructor

            Args
                listing (list): list of file names.
                prefix (str): directory prefix to be appended to file name.
                dry_run (bool): flag for test mode (no save in database).
                directory_path (str): parent directory of the songs.
                progress_show (bool): show the progress bar.
                no_add_on_error (bool): when true do not add song when parse
                    fails.
                custom_parser (module): name of a custom python module used to
                    extract data from file name; soo notes below.
                metadata_parser (str): name of the metadata parser to use
                    ('ffprobe', 'mediainfo' or `None`).
                stdout: standard output.
                stderr: standard error.

            About custom_parser:
                This module should define a method called `parse_file_name`
                which takes a file name as argument and return a dictionnary
                with the following:
                    title_music (str): title of the music.
                    detail (str): details about the music.
                    artists (list): of (str): list of artists.
                    title_work (str): name of the work related to this song.
                    subtitle_work (str): subname of the work related to this
                        song.
                    link_type (str): enum (OP ED IS IN) type of relation
                        between the work and the song.
                    link_nb (int): for OP and ED link type, number of OP or ED.

                All of these values, except `title_music`, are optional; if a
                    value is not used, set it to `None`.
        """
        if not isinstance(listing, (list, tuple)):
            raise ValueError("listing argument must be a list or a tuple")

        # if len(listing) and not isinstance(listing[0], DatabaseFeederEntry):
        #     raise ValueError("listing argument elements must be \
        #             DatabaseFeederEntry objects")

        self.listing = listing
        self.prefix = prefix
        self.dry_run = dry_run
        self.directory_path = directory_path
        self.progress_show = progress_show
        self.no_add_on_error = no_add_on_error
        self.custom_parser = custom_parser
        self.stdout = stdout
        self.stderr = stderr
        self.metadata_parser = DatabaseFeeder.select_metadata_parser(metadata_parser)

        # metadata parser
    @staticmethod
    def select_metadata_parser(parser_name):
        if parser_name is None:
            return MetadataParser

        if parser_name == 'ffprobe':
            if not FFProbeMetadataParser.is_available():
                raise CommandError("ffprobe is not available")

            return FFProbeMetadataParser

        if parser_name == 'mediainfo':
            if not MediainfoMetadataParser.is_available():
                raise CommandError("mediainfo is not available")

            return MediainfoMetadataParser

        raise CommandError("Unknown metadata parser: '{}'".format(parser_name))

    @classmethod
    def from_directory(
            cls,
            directory_path,
            *args,
            prefix="",
            append_only=False,
            progress_show=False,
            **kwargs
            ):
        """ Overloaded constructor
            Extract files from directory

            Args:
                directory_path (str): path of directory to extract songs from.

            Returns:
                (DatabaseFeeder) list of songs.
        """
        # directory
        directory_path_encoded = directory_path.encode(file_coding)
        if not os.path.isdir(directory_path_encoded):
            raise CommandError("Directory '{}' does not exist"\
                    .format(directory_path))

        directory = os.listdir(directory_path_encoded)

        listing = []

        # select metadata parser
        parser_kwarg = {}
        if 'metadata_parser' in kwargs:
            parser_kwarg['metadata_parser'] = \
                    DatabaseFeeder.select_metadata_parser(
                            kwargs['metadata_parser']
                            )

        # create progress bar
        text = "Collecting files"
        progress_bar = get_progress_bar(progress_show)
        bar = progress_bar(max_value=len(directory), text=text)

        for file_name_encoded in bar(directory):
            file_name = file_name_encoded.decode(file_coding)
            if file_is_valid(directory_path, file_name,
                    directory_path_encoded, file_name_encoded):

                entry = DatabaseFeederEntry(file_name, prefix, **parser_kwarg)

                if entry.created or not append_only:
                    listing.append(entry)

        return cls(
                listing,
                *args,
                directory_path=directory_path,
                prefix=prefix,
                progress_show=progress_show,
                **kwargs
                )

    def _get_progress_bar(self, text=None):
        """ Get the progress bar according to the verbosity requested

            Args:
                text (str): text to add to the progress bar.

            Returns:
                Progress bar object.
        """
        return get_progress_bar(self.progress_show, text)


    def set_from_file_name(self):
        """ Extract database fields from files name
        """

        # create progress bar
        text = "Extracting data from files name"
        progress_bar = self._get_progress_bar()
        bar = progress_bar(max_value=len(self.listing), text=text)

        # list of error ids
        error_ids = []

        for entry in bar(self.listing):

            try:
                entry.set_from_file_name(self.custom_parser)

            except DatabaseFeederEntryError as error:
                warnings.warn("Cannot parse file '{file_name}': {error}"\
                        .format(
                    file_name=entry.file_name,
                    error=error
                    ))

                error_ids.append(entry.song.id)

        if self.no_add_on_error:
            self.listing = [item for item in self.listing \
                    if item.song.id not in error_ids]

    def set_from_metadata(self):
        """ Extract database fields from files metadata
        """

        # create progress bar
        text = "Extracting data from files metadata"
        progress_bar = self._get_progress_bar()
        bar = progress_bar(max_value=len(self.listing), text=text)

        for entry in bar(self.listing):
            entry.set_from_metadata(self.directory_path)

    def set_from_meta_data(self):
        """ Extract database fields from files metadata
        """

        # create progress bar
        text = "Extracting data from files metadata"
        progress_bar = self._get_progress_bar()
        bar = progress_bar(max_value=len(self.listing), text=text)

        for entry in bar(self.listing):
            entry.set_from_meta_data()

    def save(self):
        """ Save list in database

            Depending on the attribute `dry_run`, entries will be saved or
            just displayed on screen.
        """

        # create progress bar
        text = "Entries to save" if self.dry_run \
                else "Saving entries to database"

        # the progress bar is displayed only if requested and if we actually
        # save the songs (instead of displaying them)
        progress_bar = get_progress_bar(
                self.progress_show and not self.dry_run
                )

        bar = progress_bar(max_value=len(self.listing), text=text)

        if self.dry_run:
            def save(obj):
                obj.show(self.stdout)

        else:
            def save(obj):
                obj.save()

        for entry in bar(self.listing):
            save(entry)


class DatabaseFeederEntry:
    """ Class representing a song to upgrade or create in the database
    """

    def __init__(self, file_name, prefix="", metadata_parser=MetadataParser):
        """ Constructor
            Detect if a song already exists in the database,
            then take it or create it

            Args:
                file_name (str): name of the song file.
                prefix (str): prefix to append to file name.
                metadata_parser (:obj:`MetadataParser`): metadata parser class.
                input arguments are aimed to serve as ID.
        """
        file_path = os.path.join(prefix, file_name)

        song, created = Song.objects.get_or_create(file_path=file_path)
        self.file_name = file_name
        self.created = created
        self.song = song
        self.metadata_parser = metadata_parser

    def set_from_file_name(self, custom_parser):
        """ Set attributes by extracting them from file name

            Args:
                custom_parser (module): module for custom parsing.
        """
        file_name, _ = os.path.splitext(self.file_name)

        self.song.title = file_name
        self.title_work = None
        self.subtitle_work = None
        self.link_type = None
        self.link_nb = None
        self.artists = None
        self.work_type_name = None
        self.work_type_query_name = None
        self.tags = None

        if custom_parser:
            try:
                data = custom_parser.parse_file_name(file_name)

            except Exception as error:
                raise DatabaseFeederEntryError(
                        "{klass}: {message}".format(
                            message=str(error),
                            klass=error.__class__.__name__
                            )

                        ) from error

            self.song.title = data.get('title_music')
            self.song.version = data.get('version')
            self.song.detail = data.get('detail')
            self.song.detail_video = data.get('detail_video')
            self.title_work = data.get('title_work')
            self.subtitle_work = data.get('subtitle_work')
            self.work_type_name = data.get('work_type_name')
            self.work_type_query_name = data.get('work_type_query_name')
            self.link_type = data.get('link_type')
            self.link_nb = data.get('link_nb')
            self.episodes = data.get('episodes')
            self.artists = data.get('artists')
            self.tags = data.get('tags')

    def set_from_metadata(self, directory_path):
        """ Set attributes by extracting them from metadata

            Args:
                directory_path (str): parent directory of the file.
        """
        file_path = os.path.join(directory_path, self.file_name)
        metadata = self.metadata_parser.parse(file_path)
        self.song.duration = metadata.duration

    def show(self, stdout=sys.stdout):
        """ Show the song content
        """
        stdout.write('')
        entry_serializer = SongSerializer(self.song)

        # get screen size
        width, _ = progressbar.utils.get_terminal_size()
        # set length to one quarter of terminal width or 20
        length = max(int(width * 0.25), 20)

        for key, value in entry_serializer.data.items():
            stdout.write("{key:{length}s} {value}".format(
                key=key,
                value=repr(value),
                length=length
                )
            )

    def save(self):
        """ Save song in database.
        """
        self.song.save()

        # Create link to work if there is one
        if self.title_work:
            if self.work_type_name and self.work_type_query_name:
                work_type, created = WorkType.objects.get_or_create(
                        name=self.work_type_name,
                        query_name=self.work_type_query_name
                        )

            else:
                work_type = None

            work, created = Work.objects.get_or_create(
                    title=self.title_work,
                    subtitle=self.subtitle_work,
                    work_type=work_type
                    )

            link, created_link = SongWorkLink.objects.get_or_create(song_id = self.song.id, work_id = work.id)
            if self.link_type:
                link.link_type = self.link_type

            if self.link_nb:
                link.link_type_number = int(self.link_nb)

            else:
                link.link_type_number = None

            if self.episodes:
                link.episodes = self.episodes

            link.save()

        # Create tags to song if there are any
        if self.tags:
            for tag_name in self.tags:
                tag, created = SongTag.objects.get_or_create(name=tag_name)
                self.song.tags.add(tag)

        # Create link to artists if there are any
        if self.artists:
            for artist_name in self.artists:
                artist, created = Artist.objects.get_or_create(name=artist_name)
                self.song.artists.add(artist)


class DatabaseFeederEntryError(Exception):
    """ Class for handling errors raised when dealing with
        a file gathered by the feeder
    """


def file_is_valid(directory_path, file_name, directory_path_encoded, file_name_encoded):
    """ Check the file validity

        A valid file is:
            A valid file,
            A media file,
            Not a hidden file.

        Args:
            directory_path (str): path to tthe directory of the file.
            file_name (str): name of the file.
            directory_path_encoded (byte): path to the directory of the file.
            file_name_encoded (byte): name of the file.

        Returns:
            (bool) true if the file is valid.
    """
    return all((
        # valid file
        os.path.isfile(os.path.join(
            directory_path_encoded,
            file_name_encoded
            )),

        # media file
        os.path.splitext(file_name)[1] not in (
            '.ssa', '.ass', '.srt', '.db'
            ),

        # not hidden file
        file_name[0] != ".",
        ))


class TextProgressBar(progressbar.ProgressBar):
    """ Progress bar with text in the widgets
    """
    def __init__(self, *args, text=None, **kwargs):
        """ Constructor

            Args:
                text (str): text to display at the left of the line.
        """
        super(TextProgressBar, self).__init__(*args, **kwargs)

        # customize the widget if text is provided
        if text is not None:
            # space padded length for text
            width, _ = progressbar.utils.get_terminal_size()
            # set length to one quarter of terminal width
            length = int(width * 0.25)

            # truncate text if necessary
            if len(text) > length:
                half = int(length * 0.5)
                text = text[:half - 2].strip() + '...' + text[-half + 1:].strip()

            widgets = [
                    "{:{length}s} ".format(text, length=length)
                    ]

            widgets.extend(self.default_widgets())
            self.widgets = widgets


class TextNullBar(progressbar.NullBar):
    """ Muted bar wich displays one line of text instead.
    """
    def __init__(self, *args, text=None, **kwargs):
        """ Constructor

            Args:
                text (str): text to display.
        """
        super(TextNullBar, self).__init__(*args, **kwargs)
        self.text = text

        if self.text:
            print(self.text)


def get_progress_bar(show, text=None):
    """ Get the progress bar class according to the requested verbosity

        Args:
            show (bool): true for enabling the progressbar display.

        Returns:
            Progress bar object.
        """
    return TextProgressBar if show else TextNullBar


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


class Command(BaseCommand):
    """ Command available for `manage.py` for feeding the library database
    """
    help = "Import songs from files."

    def add_arguments(self, parser):
        """ Extend arguments for the command
        """
        parser.add_argument(
                "directory",
                help="Path of the directory to scan."
                )

        parser.add_argument(
                "-p",
                "--prefix",
                help="Prefix to add to file path stored in database.",
                )

        parser.add_argument(
                "--parser",
                help="Name of a custom python module used to extract data from \
file name; see internal doc for what is expected for this module.",
                default=None
                )

        parser.add_argument(
                "--dry-run",
                help="Run script in test mode, don't save anything in database.",
                action="store_true",
                )

        parser.add_argument(
                "--auto-prefix",
                help="Use directory as prefix.",
                action="store_true",
                )

        parser.add_argument(
                "--append-only",
                help="Create new songs, don't update existing ones.",
                action="store_true"
                )

        parser.add_argument(
                "--no-progress",
                help="Don't display progress bars.",
                action="store_true"
                )

        parser.add_argument(
                "--debug-sql",
                help="Show Django SQL logs (very verbose).",
                action="store_true"
                )

        parser.add_argument(
                "--no-add-on-error",
                help="Do not add file when parse failed. \
By default parse error still add the file unparsed.",
                action="store_true"
                )

        parser.add_argument(
                "--metadata-parser",
                help="Which program to extract metadata: \
none, mediainfo or ffprobe (default)",
                default='ffprobe'
                )

    def handle(self, *args, **options):
        """ Process the feeding
        """

        if options.get('debug_sql'):
            logger = logging.getLogger('django.db.backends')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())

        prefix = options.get('prefix') or ""
        if options.get('auto_prefix'):
            prefix = os.path.basename(os.path.normpath(options['directory']))


        custom_parser = None
        if options.get('parser'):
            # import ipdb
            # ipdb.set_trace()
            parser_directory = os.path.join(
                    os.getcwd(),
                    os.path.dirname(options['parser'])
                    )

            parser_name, _ = os.path.splitext(os.path.basename(options['parser']))
            sys.path.append(parser_directory)
            custom_parser = importlib.import_module(parser_name)

        metadata_parser = options.get('metadata_parser')
        if metadata_parser == 'none':
            metadata_parser = None

        database_feeder = DatabaseFeeder.from_directory(
                directory_path=options['directory'],
                prefix=prefix,
                dry_run=options.get('dry_run'),
                append_only=options.get('append_only'),
                progress_show=not options.get('no_progress'),
                custom_parser=custom_parser,
                no_add_on_error=options.get('no_add_on_error'),
                metadata_parser=metadata_parser,
                stdout=self.stdout,
                stderr=self.stderr
                )

        database_feeder.set_from_file_name()
        database_feeder.set_from_metadata()
        database_feeder.save()
