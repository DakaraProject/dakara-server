#!/usr/bin/env python3
##
# Dakara Project
#
# Script to replace directories in the database
#

from progressbar import ProgressBar
from django.core.management.base import BaseCommand, CommandError
from library.models import Song

class Command(BaseCommand):
    """ Command to replace directories in the database
    """
    help = "Replace the directory field for songs."

    def add_arguments(self, parser):
        """ Extend arguments for the command
        """
        parser.add_argument(
                "source",
                help="Directory to replace."
                )

        parser.add_argument(
                "destination",
                help="New directory."
                )

    def handle(self, *args, **options):
        """ Process the directory renaming
        """
        songs = Song.objects.filter(directory=options['source'])

        if not songs:
            self.stdout.write("No songs have this directory, nothing to do")
            return

        bar = ProgressBar(max_value=songs.count())
        for song in bar(songs):
            song.directory = options['destination']
            song.save()
