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
            first_file_filename = "The first file.mp4"
            with open(os.path.join(dirpath, first_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second file.mp4"
            with open(os.path.join(dirpath, second_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command
            args = [dirpath]
            opts = {'no_progress': True}
            call_command('feed', *args, **opts)

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, '')
            self.assertEqual(songs[0].title, os.path.splitext(first_file_filename)[0])
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, '')
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
            first_file_filename = "The first file.mp4"
            with open(os.path.join(dirpath, first_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second file.mp4"
            with open(os.path.join(dirpath, second_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command
            # Join with empty string to add a trailing slash if it's not already there
            args = [os.path.join(dirpath, '')]
            opts = {'no_progress': True}
            call_command('feed', *args, **opts)

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, '')
            self.assertEqual(songs[0].title, os.path.splitext(first_file_filename)[0])
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, '')
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
            first_file_filename = "The first song name - Artist name.mp4"
            with open(os.path.join(dirpath, first_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second song name - Artist name.mp4"
            with open(os.path.join(dirpath, second_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command
            args = [dirpath]
            opts = {'parser': "library/parser_test.py", 'no_progress': True}
            call_command('feed', *args, **opts)


            artists = Artist.objects.order_by('name')
            self.assertEqual(len(artists), 1)
            artist = artists[0]
            self.assertEqual(artist.name, "Artist name")

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, '')
            self.assertEqual(songs[0].title, "The first song name")
            self.assertEqual(len(songs[0].artists.all()), 1)
            self.assertEqual(songs[0].artists.all()[0].id, artist.id)
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, '')
            self.assertEqual(songs[1].title, "The second song name")
            self.assertEqual(len(songs[1].artists.all()), 1)
            self.assertEqual(songs[1].artists.all()[0].id, artist.id)

    def test_feed_command_rename(self):
        """
        Test feed command when a file has been renamed
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            # create the first file
            first_file_filename = "The first file.mp4"
            first_file_filepath = os.path.join(dirpath, first_file_filename)

            with open(first_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # create the second file
            second_file_filename = "The second file.mp4"
            second_file_filepath = os.path.join(dirpath, second_file_filename)
            with open(second_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # call command first to populate
            args = [dirpath]
            opts = {'no_progress': True}
            call_command('feed', *args, **opts)

            # 2 files should exist
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            first_song = songs[0]
            second_song = songs[1]

            # check the databases entries are conform with the files
            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, '')
            self.assertEqual(first_song.title, os.path.splitext(first_file_filename)[0])
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, '')
            self.assertEqual(second_song.title, os.path.splitext(second_file_filename)[0])

            # suddenly, rename the first file
            first_file_filename_new = "The first new file.mp4"
            first_file_filepath_new = os.path.join(dirpath, first_file_filename_new)
            os.rename(first_file_filepath, first_file_filepath_new)

            # call command first to populate
            args = [dirpath]
            opts = {'no_progress': True}
            call_command('feed', *args, **opts)

            # there should be still 2 entries in the database
            # since its filename is close enough to the original filename
            songs = Song.objects.order_by('title')
            first_song_new = songs[0]
            second_song_new = songs[1]
            self.assertEqual(len(songs), 2)

            # check new first file, which is the same as initial first file
            # the identity is checked by ID
            self.assertEqual(first_song_new.id, first_song.id)
            self.assertEqual(first_song_new.filename, first_file_filename_new)
            self.assertEqual(first_song_new.directory, '')
            self.assertEqual(first_song_new.title,
                    os.path.splitext(first_file_filename_new)[0])

            # check second file which has not changed
            self.assertEqual(second_song_new.filename, second_file_filename)
            self.assertEqual(second_song_new.directory, '')
            self.assertEqual(second_song_new.title,
                    os.path.splitext(second_file_filename)[0])

    def test_feed_command_rename_different(self):
        """
        Test feed command when a file has been completely renamed
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            first_file_filename = "The first file.mp4"
            first_file_filepath = os.path.join(dirpath, first_file_filename)
            with open(first_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second file.mp4"
            second_file_filepath = os.path.join(dirpath, second_file_filename)
            with open(second_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command first to populate
            args = [dirpath]
            opts = {'no_progress': True}
            call_command('feed', *args, **opts)

            # basic test: the two files are in database as expected
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            first_song = songs[0]
            second_song = songs[1]
            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, '')
            self.assertEqual(first_song.title, os.path.splitext(first_file_filename)[0])
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, '')
            self.assertEqual(second_song.title, os.path.splitext(second_file_filename)[0])

            # now, rename the first file
            first_file_filename_new = "Something completely different.mp4"
            first_file_filepath_new = os.path.join(dirpath, first_file_filename_new)
            os.rename(first_file_filepath, first_file_filepath_new)

            # call command first to populate
            args = [dirpath]
            opts = {'no_progress': True}
            call_command('feed', *args, **opts)

            # there should be 3 files, because the new one is too different
            # from before
            songs = Song.objects.order_by('title')
            first_song_new = songs[0]
            first_song_old = songs[1]
            second_song_new = songs[2]
            self.assertEqual(len(songs), 3)

            # the new first file
            self.assertEqual(first_song_new.filename, first_file_filename_new)
            self.assertEqual(first_song_new.directory, '')
            self.assertEqual(first_song_new.title,
                    os.path.splitext(first_file_filename_new)[0])

            # the old first file, which file does not exist anymore
            # check the ID for identification
            self.assertEqual(first_song_old.filename, first_file_filename)
            self.assertEqual(first_song_old.id, first_song.id)
            self.assertEqual(first_song_old.directory, '')
            self.assertEqual(first_song_old.title,
                    os.path.splitext(first_file_filename)[0])

            # the second file, which has not changed
            self.assertEqual(second_song_new.filename, second_file_filename)
            self.assertEqual(second_song_new.directory, '')
            self.assertEqual(second_song_new.title,
                    os.path.splitext(second_file_filename)[0])

    def test_feed_command_directory_change(self):
        """
        Test feed command
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            # create subdirectories
            first_directory = 'first'
            second_directory = 'second'

            os.mkdir(os.path.join(dirpath, first_directory))
            os.mkdir(os.path.join(dirpath, second_directory))

            # create 2 file in first directory
            first_file_filename = "The first file.mp4"
            first_file_filepath = os.path.join(dirpath, first_directory,
                first_file_filename)

            with open(first_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second file.mp4"
            second_file_filepath = os.path.join(dirpath, first_directory,
                second_file_filename)

            with open(second_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # create 1 file in second directory
            third_file_filename = "The third file.mp4"
            third_file_filepath = os.path.join(dirpath, second_directory,
                third_file_filename)

            with open(third_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # call command on each subdirectories
            args = [dirpath]
            opts = {'no_progress': True, 'directory': first_directory}
            call_command('feed', *args, **opts)

            args = [dirpath]
            opts = {'no_progress': True, 'directory': second_directory}
            call_command('feed', *args, **opts)

            # there should be 3 songs
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 3)
            first_song = songs[0]
            second_song = songs[1]
            third_song = songs[2]

            # check first song
            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, first_directory)

            # check second song
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, first_directory)

            # check third song
            self.assertEqual(third_song.filename, third_file_filename)
            self.assertEqual(third_song.directory, second_directory)

            # suddenly, the first file is moved to the a second directory
            os.rename(first_file_filepath, os.path.join(
                dirpath,
                second_directory,
                first_file_filename
                ))

            # call command on each subdirectories another time
            args = [dirpath]
            opts = {'no_progress': True, 'directory': first_directory}
            call_command('feed', *args, **opts)

            args = [dirpath]
            opts = {'no_progress': True, 'directory': second_directory}
            call_command('feed', *args, **opts)

            # there should be 3 songs
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 3)
            first_song_old = first_song
            first_song_new = songs[0]
            second_song = songs[1]
            third_song = songs[2]

            # the new first song is in the second directory now
            self.assertEqual(first_song_new.filename, first_file_filename)
            self.assertEqual(first_song_new.directory, second_directory)
            self.assertEqual(first_song_new.id, first_song_old.id)

            # check second song
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, first_directory)

            # check third song
            self.assertEqual(third_song.filename, third_file_filename)
            self.assertEqual(third_song.directory, second_directory)
