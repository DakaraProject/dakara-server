from django.core.management import call_command
from django.test import TestCase

from .models import Artist, Work, Song, SongWorkLink


class PruneCommandTestCase(TestCase):
    def test_prune_command_artists(self):
        """Test prune command for artists
        """
        # Create artists
        artist1 = Artist()
        artist1.name = "Artist1"
        artist1.save()

        artist2 = Artist()
        artist2.name = "Artist2"
        artist2.save()

        # Create a song linked to artist1
        song1 = Song()
        song1.title = "Song1"
        song1.save()
        song1.artists.add(artist1)

        # Pre-assertions
        artists = Artist.objects.order_by('name')
        self.assertEqual(len(artists), 2)

        # Call command
        args = []
        opts = {'quiet': True, 'artists': True}
        call_command('prune', *args, **opts)

        # Post-Assertions
        artists = Artist.objects.order_by('name')
        # Only artist1 left
        # Artist2 was removed
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0].id, artist1.id)

    def test_prune_command_works(self):
        """Test prune command for works
        """
        # Create works
        work1 = Work()
        work1.title = "Work1"
        work1.save()

        work2 = Work()
        work2.title = "Work2"
        work2.save()

        # Create a song linked to work1
        song1 = Song()
        song1.title = "Song1"
        song1.save()

        link1 = SongWorkLink()
        link1.work = work1
        link1.song = song1
        link1.link_type = 'OP'
        link1.save()

        # Pre-assertions
        works = Work.objects.order_by('title')
        self.assertEqual(len(works), 2)

        # Call command
        args = []
        opts = {'quiet': True, 'works': True}
        call_command('prune', *args, **opts)

        # Post-Assertions
        works = Work.objects.order_by('title')
        # Only work1 left
        # Work2 was removed
        self.assertEqual(len(works), 1)
        self.assertEqual(works[0].id, work1.id)
