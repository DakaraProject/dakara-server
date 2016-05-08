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
from progressbar import ProgressBar
from pymediainfo import MediaInfo
from datetime import timedelta
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dakara_server.settings")
package_path = os.path.dirname(__file__)
sys.path.append(
        os.path.join(
            package_path,
            os.pardir,
            "dakara_server"
            )
        )

try:
    from library.models import * 
    from library.serializers import SongSerializer
    from django.test.client import RequestFactory
    import django

except ImportError as e:
    print("Unable to import Django modules:\n" + str(e))
    exit(1)

file_coding = sys.getfilesystemencoding()
context_dummy = dict(request=RequestFactory().get('/'))
django.setup()


class DatabaseFeeder:
    """ Class representing a list of DatabaseFeederEntry to feed the database with
    """

    def __init__(
            self,
            listing,
            prefix="",
            dry_run=False,
            directory_path="",
            progress_show=False,
            custom_parser=None
            ):
        """ Constructor

            input:
                listing <list> list of file names
                prefix <str> directory prefix to be appended to file name
                dry_run <bool> flag for test mode (no save in database)
                directory_path <str> parent directory of the songs
                no_output <bool> disable all outputs
        """
        if type(listing) not in (list, tuple):
            raise ValueError("listing argument must be a list or a tuple")

        if len(listing) and not isinstance(listing[0], DatabaseFeederEntry):
            raise ValueError("listing argument elements must be \
                    DatabaseFeederEntry objects")

        self.listing = listing
        self.prefix = prefix
        self.dry_run = dry_run
        self.directory_path = directory_path
        self.progress_show = progress_show
        self.custom_parser = custom_parser

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

            input:
                directory_path <str> path of directory to extract songs from

            output:
                <DatabaseFeeder> list of songs
        """
        directory_path_encoded = directory_path.encode(file_coding)
        directory = os.listdir(directory_path_encoded)
        listing = []
        created_amount = 0
        print("Collecting files")
        if progress_show:
            progress = ProgressBar(max_value=len(directory)).start()

        for i, file_name_encoded in enumerate(directory):
            if progress_show:
                progress.update(i + 1)

            file_name = file_name_encoded.decode(file_coding)
            if \
                    os.path.isfile(os.path.join(
                        directory_path_encoded,
                        file_name_encoded
                        )) and \
                    os.path.splitext(file_name)[1] not in (
                        '.ssa', '.ass', '.srt', '.db'
                        ) and \
                    file_name[0] != ".":
                entry = DatabaseFeederEntry(file_name, prefix)
                if entry.created or not append_only:
                    listing.append(entry)

                if entry.created:
                    created_amount += 1

        if progress_show:
            progress.finish()

        if created_amount:
            print("{} new song{} detected".format(
                created_amount,
                "s" if created_amount > 1 else ""
                ))

        return cls(
                listing,
                *args,
                directory_path=directory_path,
                prefix=prefix,
                progress_show=progress_show,
                **kwargs
                )

    def set_from_file_name(self):
        """ Extract database fields from files name
        """
        print("Extracting data from files name")
        if self.progress_show:
            progress = ProgressBar(max_value=len(self.listing)).start()

        for i, entry in enumerate(self.listing):
            if self.progress_show:
                progress.update(i + 1)
            entry.set_from_file_name(self.custom_parser)

        if self.progress_show:
            progress.finish()

    def set_from_media_info(self):
        """ Extract database fields from files media info
        """
        print("Extracting data from files media info")
        if self.progress_show:
            progress = ProgressBar(max_value=len(self.listing)).start()

        for i, entry in enumerate(self.listing):
            if self.progress_show:
                progress.update(i + 1)
            entry.set_from_media_info(self.directory_path)

        if self.progress_show:
            progress.finish()

    def set_from_meta_data(self):
        """ Extract database fields from files metadata
        """
        print("Extracting data from files metadata")
        if self.progress_show:
            progress = ProgressBar(max_value=len(self.listing)).start()

        for i, entry in enumerate(self.listing):
            if self.progress_show:
                progress.update(i + 1)
            entry.set_from_meta_data()

        if self.progress_show:
            progress.finish()

    def save(self):
        """ Save list in database
        """
        if self.dry_run:
            print("Entries to save")

        else:
            print("Saving entries to database")

        if self.progress_show and not self.dry_run:
            progress = ProgressBar(max_value=len(self.listing)).start()

        for i, entry in enumerate(self.listing):
            if self.dry_run:
                self._save_dry_run(entry)

            else:
                self._save_real(entry)
                if self.progress_show:
                    progress.update(i + 1)

        if self.progress_show and not self.dry_run:
            progress.finish()

    def _save_real(self, entry):
        """ Real save process
        """
        entry.save()

    def _save_dry_run(self, entry):
        """ Simulated save process
        """
        entry_serializer = SongSerializer(entry.song, context=context_dummy)
        print()
        for key, value in entry_serializer.data.items():
            print(key, ":", value)


class DatabaseFeederEntry:
    """ Class representing a song to upgrade or create in the database
    """

    def __init__(self, file_name, prefix=""):
        """ Constructor
            Detect if a song already exists in the database,
            then take it or create it

            input:
                file_name <str> name of the song file
                prefix <str> prefix to append to file name
                input arguments are aimed to serve as ID
        """
        file_path = os.path.join(prefix, file_name)
        try:
            song = Song.objects.get(file_path=file_path)
            created = False

        except Song.DoesNotExist:
            song = Song(file_path=file_path)
            created = True

        self.file_name = file_name
        self.created = created
        self.song = song

    def set_from_file_name(self, custom_parser):
        """ Set attributes by extracting them from file name
        """
        file_name = os.path.splitext(self.file_name)[0]

        self.song.title = file_name
        self.title_work = None
        self.subtitle_work = None
        self.link_type = None 
        self.link_nb = None
        self.artists = None

        if custom_parser:
            data = custom_parser.parse_file_name(file_name)
            self.song.title = data['title_music']
            self.song.detail = data['detail']
            self.title_work = data['title_work']
            self.subtitle_work = data['subtitle_work']
            self.link_type = data['link_type'] 
            self.link_nb = data['link_nb']
            self.artists = data['artists']
            

    def set_from_media_info(self, directory_path):
        """ Set attributes by extracting them from media info

            input:
                directory_path <str> parent directory of the file
        """
        file_path = os.path.join(directory_path, self.file_name)
        media = MediaInfo.parse(file_path)
        media_general_track = media.tracks[0]
        duration = getattr(media_general_track, 'duration', 0) or 0
        self.song.duration = timedelta(milliseconds=int(duration))

    def set_from_meta_data(self):
        """ Set attributes by extracting them from file metadata
            Not implemented
        """

    def save(self):
        """ Save song in database
        """
        self.song.save()

        # Create link to work if there is one
        if self.title_work:
            work, created = Work.objects.get_or_create(title=self.title_work,subtitle=self.subtitle_work)
            link, created_link = SongWorkLink.objects.get_or_create(song_id = self.song.id, work_id = work.id)
            if self.link_type:
                link.link_type = self.link_type
            if self.link_nb:
                link.link_type_number = int(self.link_nb)
            else:
                link.link_type_number = None
            link.save()
        
        # Create link to artists if there are any
        if self.artists:
            for artist_name in self.artists:
                artist, created = Artist.objects.get_or_create(name=artist_name)
                self.song.artists.add(artist)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
            description="Import songs from files \
and feed the Django database with it"
            )
    parser.add_argument(
            "directory",
            help="path of the directory to scan"
            )
    parser.add_argument(
            "-p",
            "--prefix",
            help="prefix to add to file path stored in database"
            )
    parser.add_argument(
            "--parser",
            help="Name of a custom python module used to extract data from file name.\
                    This module should define a method called parse_file_name\
                    which takes a file name as argument and return a dictionnary with the following :\
                    title_music : (String) Title of the music.\
                    detail : (String) Details about the music.\
                    artists : (Array of String) List of artists.\
                    title_work : (String) Name of the work related to this song.\
                    subtitle_work : (String) SubName of the work related to this song.\
                    link_type : (String Enum : OP ED IS IN) Type of relation between the work and the song.\
                    link_nb : (Integer) For OP and ED link type, number of OP or ED.\
                    All of these values, except title_music are optional, if a value is not used, set it to None."
            )
    parser.add_argument(
            "-d",
            "--dry-run",
            help="run script in test mode, don't save anything in database",
            action="store_true"
            )
    parser.add_argument(
            "--auto-prefix",
            help="use directory as prefix",
            action="store_true"
            )
    parser.add_argument(
            "--append-only",
            help="create new songs, don't update existing ones",
            action="store_true"
            )
    parser.add_argument(
            "--no-progress",
            help="don't display progress bars",
            action="store_true"
            )
    parser.add_argument(
            "--debug-sql",
            help="show Django SQL logs (very verbose)",
            action="store_true"
            )

    args = parser.parse_args()

    if args.debug_sql:
        logger = logging.getLogger('django.db.backends')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

    prefix = args.prefix or ""
    if args.auto_prefix:
        prefix = os.path.basename(os.path.normpath(args.directory))
    
    custom_parser = None
    if args.parser:
        custom_parser = importlib.import_module(args.parser)

    database_feeder = DatabaseFeeder.from_directory(
            directory_path=args.directory,
            prefix=prefix,
            dry_run=args.dry_run,
            append_only=args.append_only,
            progress_show=not args.no_progress,
            custom_parser=custom_parser
            )

    database_feeder.set_from_file_name()
    database_feeder.set_from_media_info()
    database_feeder.save()
