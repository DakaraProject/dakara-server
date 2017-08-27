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
            dry_run=False,
            directory_source="",
            directory=None,
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
                directory (str): directory to store in the database.
                dry_run (bool): flag for test mode (no save in database).
                directory_source (str): parent directory of the songs.
                progress_show (bool): show the progress bar.
                no_add_on_error (bool): when true do not add song when parse
                    fails.
                custom_parser (module): name of a custom python module used to
                    extract data from file name; soo notes below.
                metadata_parser (str): name of the metadata parser to use
                    ('ffprobe', 'mediainfo' or `None`).
                stdout (file descriptor): standard output.
                stderr (file descriptor): standard error.

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

        self.listing = listing
        self.dry_run = dry_run
        self.directory_source = directory_source
        self.progress_show = progress_show
        self.no_add_on_error = no_add_on_error
        self.custom_parser = custom_parser
        self.stdout = stdout
        self.stderr = stderr
        self.metadata_parser = DatabaseFeeder.select_metadata_parser(metadata_parser)
        self.directory = DatabaseFeeder.select_directory(directory,
                directory_source)


    @staticmethod
    def select_directory(directory, directory_source):
        """ Select the directory to store in the database

            If no directory is provided, it gives the parent directory of the
            scanned songs.

            If a directory is provided as a string, it gives this string.

            If a directory is provided as a level (ie: as negative integer), it
                gives the folder structure up to this level from the directory
                of the scanned song.

            Args:
                directory (str): directory given from command.
                directory_source (str): directory of the songs to scan.

            Returns:
                (str) directory structure to store in database.
        """
        # if no directory is provided, return the last folder of directory
        # source, which is the parent directory of scanned files
        if directory is None:
            return os.path.basename(directory_source)

        # try to convert directory in numeric value, and return the string of n
        # folders ahead from directory source, which is the nth parent directory
        # of scanned files
        try:
            directory_num = int(directory)
            directory_source_list = directory_source.split(os.path.sep)

            # check if the level is negative
            if directory_num >= 0:
                raise ValueError

            # check if the level is too deep
            if -directory_num > len(directory_source_list):
                raise ValueError

            return os.path.join(*directory_source_list[directory_num:])

        # otherwize, just return the directory string
        except ValueError:
            return directory

    @staticmethod
    def select_metadata_parser(parser_name):
        """ Select the metadata parser class according to its name

            Args:
                parser_name (str): name of the parser.

            Returns:
                (:obj:`MetadataParser`) class of the parser.
        """
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
            *args,
            append_only=False,
            **kwargs
            ):
        """ Overloaded constructor
            Extract files from directory

            Args:
                directory (str): directory to store in the database.
                dry_run (bool): flag for test mode (no save in database).
                directory_source (str): parent directory of the songs.
                progress_show (bool): show the progress bar.
                no_add_on_error (bool): when true do not add song when parse
                    fails.
                custom_parser (module): name of a custom python module used to
                    extract data from file name; soo notes below.
                metadata_parser (str): name of the metadata parser to use
                    ('ffprobe', 'mediainfo' or `None`).
                stdout (file descriptor): standard output.
                stderr (file descriptor): standard error.
                append_only (bool): create only new songs, do not update
                    existing ones.

            Returns:
                (:obj:`DatabaseFeeder`) feeder object.
        """
        # create instance of feeder with no feeder entries yet
        feeder = cls([], *args, **kwargs)

        # manage directory
        directory_source_encoded = feeder.directory_source.encode(file_coding)
        if not os.path.isdir(directory_source_encoded):
            raise CommandError("Directory '{}' does not exist"\
                    .format(directory_source))

        directory = os.listdir(directory_source_encoded)

        # create progress bar
        text = "Collecting files"
        ProgressBar = feeder._get_progress_bar()
        bar = ProgressBar(max_value=len(directory), text=text)

        # scan directory
        listing = []
        for filename_encoded in bar(directory):
            filename = filename_encoded.decode(file_coding)
            if file_is_valid(feeder.directory_source, filename,
                    directory_source_encoded, filename_encoded):

                entry = DatabaseFeederEntry(
                        filename,
                        feeder.directory,
                        metadata_parser=feeder.metadata_parser
                        )

                # only add entry to feeder list if we are not in append only
                # mode, otherwise only if the entry is new in the database
                if entry.created or not append_only:
                    listing.append(entry)

        # put listing in feeder
        feeder.listing = listing

        return feeder

    def _get_progress_bar(self, show=None):
        """ Get the progress bar class according to the verbosity requested

            Checks the `progress_show` attribute.

            Args:
                show (bool): if provided, bypass the `progress_show` attribute
                    in favour of this argument.

            Returns:
                Progress bar object.
        """
        if show is None:
            show = self.progress_show

        return TextProgressBar if show else TextNullBar


    def set_from_filename(self):
        """ Extract database fields from files name
        """
        # create progress bar
        text = "Extracting data from files name"
        ProgressBar = self._get_progress_bar()
        bar = ProgressBar(max_value=len(self.listing), text=text)

        # list of erroneous songs id
        error_ids = []

        for entry in bar(self.listing):
            try:
                entry.set_from_filename(self.custom_parser)

            except DatabaseFeederEntryError as error:
                # only show a warning in case of error
                warnings.warn("Cannot parse file '{filename}': {error}"\
                        .format(
                            filename=entry.filename,
                            error=error
                            )
                        )

                error_ids.append(entry.song.id)

        # if no erroneous songs can be added, delete them from list
        if self.no_add_on_error:
            self.listing = [item for item in self.listing \
                    if item.song.id not in error_ids]

    def set_from_metadata(self):
        """ Extract database fields from files metadata
        """
        # create progress bar
        text = "Extracting data from files metadata"
        ProgressBar = self._get_progress_bar()
        bar = ProgressBar(max_value=len(self.listing), text=text)

        # extract metadata
        for entry in bar(self.listing):
            entry.set_from_metadata(self.directory_source)

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
        ProgressBar = self._get_progress_bar(
                self.progress_show and not self.dry_run
                )

        bar = ProgressBar(max_value=len(self.listing), text=text)

        # define action to perform depending on dry run mode or not
        if self.dry_run:
            def save(obj):
                obj.show(self.stdout)

        else:
            def save(obj):
                obj.save()

        # save entries
        for entry in bar(self.listing):
            save(entry)


class DatabaseFeederEntry:
    """ Class representing a song to upgrade or create in the database
    """

    def __init__(self, filename, directory, metadata_parser=None):
        """ Constructor

            Detect if a song already exists in the database, then take it or
            create a new object not yet saved.

            Args:
                filename (str): name of the song file, serves as ID.
                directory (str): directory of the song file to store in the
                    database, serves as ID.
                metadata_parser (:obj:`MetadataParser`): metadata parser class.
                    Default is `MetadataParser`.
        """
        # we do not use get_or_create as it will automatically create a new Song
        # in the database
        try:
            song = Song.objects.get(filename=filename, directory=directory)
            created = False

        except Song.DoesNotExist:
            song = Song(filename=filename, directory=directory)
            created = True

        self.filename = filename
        self.directory = directory
        self.created = created
        self.song = song

        # if no metadata parser is provided, use the default one
        self.metadata_parser = metadata_parser or MetadataParser

    def set_from_filename(self, custom_parser):
        """ Set attributes by extracting them from file name

            Args:
                custom_parser (module): module for custom parsing.
        """
        filename, _ = os.path.splitext(self.filename)

        # prepare fields
        self.song.title = filename
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
                data = custom_parser.parse_file_name(filename)

            except Exception as error:
                # re-raise the error with custom class and message
                raise DatabaseFeederEntryError(
                        "{klass}: {message}".format(
                            message=str(error),
                            klass=error.__class__.__name__
                            )

                        ) from error

            # fill fields
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

    def set_from_metadata(self, directory_source):
        """ Set attributes by extracting them from metadata

            Args:
                directory_source (str): parent directory of the file.
        """
        file_path = os.path.join(directory_source, self.filename)
        metadata = self.metadata_parser.parse(file_path)
        self.song.duration = metadata.duration

    def show(self, stdout=sys.stdout):
        """ Show the song content

            Args:
                stdout (file descriptor): standard output.
        """
        stdout.write('')

        # set key length to one quarter of terminal width or 20
        width, _ = progressbar.utils.get_terminal_size()
        length = max(int(width * 0.25), 20)

        # we cannot use the song serializer here because it will have troubles on
        # songs that are not already in the database
        # instead, we extract manually all the fields
        fields = {k: v for k, v in self.song.__dict__.items() \
                if k not in ('_state')}

        fields.update({k: v for k, v in self.__dict__.items() \
                if k not in ('filename', 'directory', 'song', 'metadata_parser')})

        for key, value in fields.items():
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

            link, created_link = SongWorkLink.objects.get_or_create(
                    song_id=self.song.id,
                    work_id=work.id
                    )

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


def file_is_valid(directory_source, filename, directory_source_encoded, filename_encoded):
    """ Check the file validity

        A valid file is:
            An existing file,
            A media file,
            Not a hidden file.

        Args:
            directory_source (str): path to tthe directory of the file.
            filename (str): name of the file.
            directory_source_encoded (byte): path to the directory of the file.
            filename_encoded (byte): name of the file.

        Returns:
            (bool) true if the file is valid.
    """
    return all((
        # valid file
        os.path.isfile(os.path.join(
            directory_source_encoded,
            filename_encoded
            )),

        # media file
        os.path.splitext(filename)[1] not in (
            '.ssa', '.ass', '.srt', '.db', '.txt',
            ),

        # not hidden file
        filename[0] != ".",
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
            # set length to one quarter of terminal width
            width, _ = progressbar.utils.get_terminal_size()
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
    help = "Import songs from directory."

    def add_arguments(self, parser):
        """ Extend arguments for the command
        """
        parser.add_argument(
                "directory-source",
                help="Path of the directory to scan."
                )

        parser.add_argument(
                "--no-progress",
                help="Don't display progress bars.",
                action="store_true"
                )

        parser.add_argument(
                "-r",
                "--dry-run",
                help="Run script in test mode, don't save anything in database.",
                action="store_true"
                )

        parser.add_argument(
                "-D",
                "--directory",
                help="Directory stored in database for the files scanned. By \
default, it will be the name of the scanned directory. If indicated as a \
negative number, it will be the directory structure up to this number ahead \
from the scanned directory. Example: for -2 and a/b/c, will give b/c. \
Overriden by the 'no-directory' option.",
                default=None
                )

        parser.add_argument(
                "--no-directory",
                help="Do not set directory for the files scanned. \
This overrides the 'directory' option.",
                action="store_true"
                )

        parser.add_argument(
                "--parser",
                help="Name of a custom python module used to extract data from \
file name; see internal doc for what is expected for this module.",
                default=None
                )

        parser.add_argument(
                "--metadata-parser",
                help="Which program to extract metadata from: \
none (no parser), mediainfo or ffprobe (default).",
                default='ffprobe'
                )

        parser.add_argument(
                "--append-only",
                help="Create new songs, don't update existing ones.",
                action="store_true"
                )

        parser.add_argument(
                "--no-add-on-error",
                help="Do not add file when parse failed. \
By default parse error still add the file unparsed.",
                action="store_true"
                )

        parser.add_argument(
                "--debug-sql",
                help="Show Django SQL logs (very verbose).",
                action="store_true"
                )

    def handle(self, *args, **options):
        """ Process the feeding
        """
        # debug SQL
        if options.get('debug_sql'):
            logger = logging.getLogger('django.db.backends')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())

        # custom parser
        custom_parser = None
        if options.get('parser'):
            parser_directory = os.path.join(
                    os.getcwd(),
                    os.path.dirname(options['parser'])
                    )

            parser_name, _ = os.path.splitext(os.path.basename(options['parser']))
            sys.path.append(parser_directory)
            custom_parser = importlib.import_module(parser_name)

        # directory
        if options.get('no_directory'):
            directory = ''

        else:
            directory = options.get('directory')
            if directory:
                # clean provided directory string
                directory = os.path.normpath(directory)

        # metadata parser
        metadata_parser = options.get('metadata_parser')
        if metadata_parser == 'none':
            metadata_parser = None

        # create feeder object
        database_feeder = DatabaseFeeder.from_directory(
                directory_source=options['directory-source'],
                directory=directory,
                dry_run=options.get('dry_run'),
                append_only=options.get('append_only'),
                progress_show=not options.get('no_progress'),
                custom_parser=custom_parser,
                no_add_on_error=options.get('no_add_on_error'),
                metadata_parser=metadata_parser,
                stdout=self.stdout,
                stderr=self.stderr
                )

        database_feeder.set_from_filename()
        database_feeder.set_from_metadata()
        database_feeder.save()