#!/usr/bin/env python3
##
# Dakara Project
#
# Script for feeding the server database with songs from a directory
#

import os
import sys
import logging
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
    from library.models import Song
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

    def __init__(self, listing, prefix="", dry_run=False, directory_path=""):
        """ Constructor

            input:
                listing <list> list of file names
                prefix <str> directory prefix to be appended to file name
                dry_run <bool> flag for test mode (no save in database)
                directory_path <str> parent directory of the songs
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

    @classmethod
    def from_directory(
            cls,
            directory_path,
            *args,
            prefix="",
            append_only=False,
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
        with ProgressBar(max_value=len(directory)) as progress:
            for i, file_name_encoded in enumerate(directory):
                progress.update(i)
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
                    if append_only and entry.created or not append_only:
                        listing.append(entry)
                    if entry.created:
                        created_amount += 1

        if created_amount:
            print("{} new song{} created".format(
                created_amount,
                "s" if created_amount > 1 else ""
                ))

        return cls(
                listing,
                *args,
                directory_path=directory_path,
                prefix=prefix,
                **kwargs
                )

    def set_from_file_name(self):
        """ Extract database fields from files name
        """
        print("Extracting data from files name")
        with ProgressBar(max_value=len(self.listing)) as progress:
            for i, entry in enumerate(self.listing):
                progress.update(i)
                entry.set_from_file_name()

    def set_from_media_info(self):
        """ Extract database fields from files media info
        """
        print("Extracting data from files media info")
        with ProgressBar(max_value=len(self.listing)) as progress:
            for i, entry in enumerate(self.listing):
                progress.update(i)
                entry.set_from_media_info(self.directory_path)

    def set_from_meta_data(self):
        """ Extract database fields from files metadata
        """
        print("Extracting data from files metadata")
        with ProgressBar(max_value=len(self.listing)) as progress:
            for i, entry in enumerate(self.listing):
                progress.update(i)
                entry.set_from_meta_data()

    def save(self):
        """ Save list in database
        """
        print("Saving entries to database")
        with ProgressBar(max_value=len(self.listing)) as progress:
            save_fun = self._save_dry_run if self.dry_run else self._save_real
            for i, entry in enumerate(self.listing):
                save_fun(entry, progress, i)

    def _save_real(self, entry, progress, iterator):
        """ Real save process
        """
        entry.save()
        progress.update(iterator)

    def _save_dry_run(self, entry, *args, **kwargs):
        """ Simulated save process
        """
        entry_serializer = SongSerializer(entry.song, context=context_dummy)
        for key, value in entry_serializer.data.items():
            print(key, ":", value)

        print()


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

    def set_from_file_name(self):
        """ Set attributes by extracting them from file name
        """
        self.song.title = os.path.splitext(self.file_name)[0]

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

    database_feeder = DatabaseFeeder.from_directory(
            directory_path=args.directory,
            prefix=prefix,
            dry_run=args.dry_run,
            append_only=args.append_only
            )

    database_feeder.set_from_file_name()
    database_feeder.set_from_media_info()
    database_feeder.save()
