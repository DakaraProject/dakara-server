##
# Dakaraneko Project
#
# Script for removing unused data from database 
#

import os

from django.core.management.base import BaseCommand, CommandError
from library.models import Artist, Work, Song

class Command(BaseCommand):
    """ Command available for `manage.py` for removing unused objects
        from database.
    """
    help = "Remove unused objects from database."

    def add_arguments(self, parser):
        """ Extend arguments for the command
        """

        parser.add_argument(
                "--artists",
                help="Remove artists with no songs attached.",
                action="store_true"
                )

        parser.add_argument(
                "--works",
                help="Remove works with no songs attached.",
                action="store_true"
                )

        parser.add_argument(
                "--quiet",
                help="Do not display anything on run.",
                action="store_true"
                )

    def handle(self, *args, **options):
        """ Prune database
        """

        # quiet mode
        if options['quiet']:
            self.stdout = open(os.devnull, 'w')
            self.stderr = open(os.devnull, 'w')

        # prune artists if requested
        if options['artists']:
            # TODO: starting from django 1.9 the delete method returns
            # the number of rows affected
            # so this can be done in one call
            queryset = Artist.objects.filter(song=None)
            removed_artists = queryset.count()
            queryset.delete()
            self.stdout.write("Removed {} artists.".format(removed_artists))

        # prune works if requested
        if options['works']:
            # TODO: starting from django 1.9 the delete method returns
            # the number of rows affected
            # so this can be done in one call
            queryset = Work.objects.filter(song=None)
            removed_works = queryset.count()
            queryset.delete()
            self.stdout.write("Removed {} works.".format(removed_works))

