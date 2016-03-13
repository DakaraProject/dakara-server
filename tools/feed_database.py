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
except ImportError as e:
    print("Unable to import Django modules:\n" + str(e))
    exit(1)

file_coding = sys.getfilesystemencoding()


class FeedDatabase:
    """ Class representing a list of files to feed the database with
    """

    def __init__(self, listing, prefix="", test=False, directory=""):
        """ Constructor

            input:
                listing <list> list of file names
                prefix <str> directory prefix to be appended to file name
                test <bool> flag for test mode (no save in database)
        """
        self.listing_raw = listing
        self.prefix = prefix
        self.test = test
        self.listing = []
        self.directory = directory

    @classmethod
    def from_directory(cls, directory_path, *args, **kwargs):
        """ Overloaded constructor
            Extract files from directory

            input:
                directory_path <str> path of directory to extract songs

            output:
                <object> FeedDatabase object
        """
        directory_path_encoded = directory_path.encode(file_coding)
        directory = os.listdir(directory_path_encoded)
        listing = []
        print("Collecting files")
        with ProgressBar(max_value=len(directory)) as progress:
            for i, file in enumerate(directory):
                progress.update(i)
                file_decoded = file.decode(file_coding)
                if os.path.isfile(
                        os.path.join(directory_path_encoded, file)
                        ) and \
                        os.path.splitext(file_decoded)[1] not in (
                                '.ssa', '.ass', '.srt', '.db'
                                ) and \
                        file_decoded[0] != ".":
                    listing.append(file_decoded)
        return cls(listing, *args, directory=directory_path, **kwargs)

    def extract_attributes(self):
        """ Extract database fields from files
        """

        listing = []
        print("Extracting data from files")
        with ProgressBar(max_value=len(self.listing_raw)) as progress:
            for i, file in enumerate(self.listing_raw):
                progress.update(i)
                title = os.path.splitext(file)[0]
                file_path = os.path.join(self.directory, file)
                media = MediaInfo.parse(file_path)
                media_general_track = media.tracks[0]
                duration = getattr(media_general_track, 'duration', 0) or 0
                listing.append((title, file, duration))
        self.listing = listing

    def save(self):
        """ Save list in database
        """
        print("Saving entries to database")
        with ProgressBar(max_value=len(self.listing)) as progress:
            for i, (title, file, duration) in enumerate(self.listing):
                file_path = os.path.join(self.prefix, file)
                song = Song(
                        title=title,
                        file_path=file_path,
                        duration=timedelta(milliseconds=int(duration))
                        )
                if not self.test:
                    progress.update(i)
                    song.save()
                else:
                    print(
                            "Title: " + title +
                            "\nPath: " + file_path +
                            "\nDuration: " + str(duration) +
                            "\n"
                            )


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
            "-t",
            "--test-mode",
            help="run script in test mode, don't save anything in database",
            action="store_true"
            )
    parser.add_argument(
            "-a",
            "--auto-prefix",
            help="use directory-name as prefix",
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

    feed_database = FeedDatabase.from_directory(
            directory_path=args.directory,
            prefix=prefix,
            test=args.test_mode

            )
    feed_database.extract_attributes()
    feed_database.save()
