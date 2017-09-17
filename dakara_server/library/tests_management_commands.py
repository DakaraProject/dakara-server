from tempfile import NamedTemporaryFile, TemporaryDirectory
import os
from django.core.management import call_command
from django.test import TestCase
from .models import WorkType, SongTag, Song, Artist

class QueryLanguageParserTestCase(TestCase):

    def test_createtags_command(self):
        """
        Test create tags command
        """
        # Pre-Assertions
        tags = SongTag.objects.order_by('name')
        self.assertEqual(len(tags), 0)

        file_content = """tags:
  - name: TAGNAME1
    color_id: 0
  - name: TAGNAME2
    color_id: 5"""

        # Create temporary config file
        with NamedTemporaryFile(mode='wt') as config_file:
            config_file.write(file_content)
            config_file.flush()

            # Call command
            args = [config_file.name]
            opts = {}
            call_command('createtags', *args, **opts)

            # Post-Assertions
            tags = SongTag.objects.order_by('name')
            self.assertEqual(len(tags), 2)
            self.assertEqual(tags[0].name, "TAGNAME1")
            self.assertEqual(tags[0].color_id, 0)
            self.assertEqual(tags[1].name, "TAGNAME2")
            self.assertEqual(tags[1].color_id, 5)

    def test_createworktypes_command(self):
        """
        Test create work types command
        """
        # Pre-Assertions
        work_types = WorkType.objects.order_by('query_name')
        self.assertEqual(len(work_types), 0)

        file_content = """worktypes:
  - query_name: work-type-one
    name: Work type one
    icon_name: elephant
  - query_name: work-type-two
    name: Work type two
    icon_name: cat"""

        # Create temporary config file
        with NamedTemporaryFile(mode='wt') as config_file:
            config_file.write(file_content)
            config_file.flush()

            # Call command
            args = [config_file.name]
            opts = {}
            call_command('createworktypes', *args, **opts)

            # Post-Assertions
            work_types = WorkType.objects.order_by('query_name')
            self.assertEqual(len(work_types), 2)
            self.assertEqual(work_types[0].query_name, "work-type-one")
            self.assertEqual(work_types[0].name, "Work type one")
            self.assertEqual(work_types[0].icon_name, "elephant")
            self.assertEqual(work_types[1].query_name, "work-type-two")
            self.assertEqual(work_types[1].name, "Work type two")
            self.assertEqual(work_types[1].icon_name, "cat")

    def test_feed_command(self):
        """
        Test feed command
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            dirname = os.path.basename(dirpath)

            first_file_filename = "The first file.mp4"
            with open(os.path.join(dirpath, first_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second file.mp4"
            with open(os.path.join(dirpath, second_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command
            args = [dirpath]
            opts = {}
            call_command('feed', *args, **opts)

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, dirname)
            self.assertEqual(songs[0].title, os.path.splitext(first_file_filename)[0])
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, dirname)
            self.assertEqual(songs[1].title, os.path.splitext(second_file_filename)[0])

    def test_feed_command_with_trailing_slash(self):
        """
        Test feed command when path contains a trailling slash
        There was a bug, when a path with trailing slash was given,
        The directory field was empty instead of containing the containing folder name
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            dirname = os.path.basename(dirpath)

            first_file_filename = "The first file.mp4"
            with open(os.path.join(dirpath, first_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second file.mp4"
            with open(os.path.join(dirpath, second_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command
            # Join with empty string to add a trailing slash if it's not already there
            args = [os.path.join(dirpath, '')]
            opts = {}
            call_command('feed', *args, **opts)

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, dirname)
            self.assertEqual(songs[0].title, os.path.splitext(first_file_filename)[0])
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, dirname)
            self.assertEqual(songs[1].title, os.path.splitext(second_file_filename)[0])

    def test_feed_command_with_parser(self):
        """
        Test feed command with parser
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)
        artists = Artist.objects.order_by('name')
        self.assertEqual(len(artists), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            dirname = os.path.basename(dirpath)

            first_file_filename = "The first song name - Artist name.mp4"
            with open(os.path.join(dirpath, first_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second song name - Artist name.mp4"
            with open(os.path.join(dirpath, second_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command
            args = [dirpath]
            opts = {'parser': "library/parser_test.py"}
            call_command('feed', *args, **opts)


            artists = Artist.objects.order_by('name')
            self.assertEqual(len(artists), 1)
            artist = artists[0]
            self.assertEqual(artist.name, "Artist name")

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, dirname)
            self.assertEqual(songs[0].title, "The first song name")
            self.assertEqual(len(songs[0].artists.all()), 1)
            self.assertEqual(songs[0].artists.all()[0].id, artist.id)
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, dirname)
            self.assertEqual(songs[1].title, "The second song name")
            self.assertEqual(len(songs[1].artists.all()), 1)
            self.assertEqual(songs[1].artists.all()[0].id, artist.id)
