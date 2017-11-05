from tempfile import NamedTemporaryFile, TemporaryDirectory
import os
import shutil
import unittest
from django.core.management import call_command
from django.test import TestCase
from .models import WorkType, SongTag, Song, Artist
from .management.commands.feed import FFmpegWrapper

RESSOURCES_DIR = "tests_ressources"
SUBTITLES_DIR = "subtitles"
APP_DIR = os.path.dirname(os.path.abspath(__file__))

class CommandsTestCase(TestCase):

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
            opts = {'quiet': True}
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
    name_plural: Work type one plural
    icon_name: elephant
  - query_name: work-type-two
    name: Work type two
    name_plural: Work type two plural
    icon_name: cat"""

        # Create temporary config file
        with NamedTemporaryFile(mode='wt') as config_file:
            config_file.write(file_content)
            config_file.flush()

            # Call command
            args = [config_file.name]
            opts = {'quiet': True}
            call_command('createworktypes', *args, **opts)

            # Post-Assertions
            work_types = WorkType.objects.order_by('query_name')
            self.assertEqual(len(work_types), 2)
            self.assertEqual(work_types[0].query_name, "work-type-one")
            self.assertEqual(work_types[0].name, "Work type one")
            self.assertEqual(work_types[0].name_plural, "Work type one plural")
            self.assertEqual(work_types[0].icon_name, "elephant")
            self.assertEqual(work_types[1].query_name, "work-type-two")
            self.assertEqual(work_types[1].name, "Work type two")
            self.assertEqual(work_types[1].name_plural, "Work type two plural")
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
            opts = {'quiet': True, 'metadata_parser': 'none'}
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
            opts = {'quiet': True, 'metadata_parser': 'none'}
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
            opts = {'parser': "library/parser_test.py", 'quiet': True, 'metadata_parser': 'none'}
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
            opts = {'quiet': True, 'metadata_parser': 'none'}
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
            opts = {'quiet': True, 'metadata_parser': 'none'}
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
            opts = {'quiet': True, 'metadata_parser': 'none'}
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
            opts = {'quiet': True, 'metadata_parser': 'none'}
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
            opts = {'quiet': True, 'metadata_parser': 'none', 'directory': first_directory}
            call_command('feed', *args, **opts)

            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none', 'directory': second_directory}
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
            opts = {'quiet': True, 'metadata_parser': 'none', 'directory': first_directory}
            call_command('feed', *args, **opts)

            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none', 'directory': second_directory}
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

    def test_feed_command_rename_and_new(self):
        """
        Test feed command when a file has been renamed
        and a new file simillar name is added
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
            opts = {'quiet': True, 'metadata_parser': 'none'}
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

            # create new file with similar name
            third_file_filename = "The zew first file.mp4"
            third_file_filepath = os.path.join(dirpath, third_file_filename)
            with open(third_file_filepath, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")


            # call command again to populate
            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none'}
            call_command('feed', *args, **opts)

            # there should be 3 entries in the database
            # since the renamed filed should be matched with its old name
            # and the new file added
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 3)
            first_song_new = songs[0]
            second_song_new = songs[1]
            third_song_new = songs[2]

            # check new first file
            self.assertEqual(first_song_new.filename, first_file_filename_new)
            self.assertEqual(first_song_new.directory, '')
            self.assertEqual(first_song_new.title,
                    os.path.splitext(first_file_filename_new)[0])

            # check second file which has not changed
            self.assertEqual(second_song_new.filename, second_file_filename)
            self.assertEqual(second_song_new.directory, '')
            self.assertEqual(second_song_new.title,
                    os.path.splitext(second_file_filename)[0])

            # check third file which is new
            self.assertEqual(third_song_new.filename, third_file_filename)
            self.assertEqual(third_song_new.directory, '')
            self.assertEqual(third_song_new.title,
                    os.path.splitext(third_file_filename)[0])

            # Check that old first file is still in database with the same id
            # and is now new first or third file
            self.assertTrue(first_song.id == first_song_new.id or first_song.id == third_song_new.id )

    def test_feed_command_prune(self):
        """
        Test feed command with prune argument
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            first_file_filename = "The first file.mp4"
            first_file_path = os.path.join(dirpath, first_file_filename)
            with open(first_file_path, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            second_file_filename = "The second file.mp4"
            second_file_path = os.path.join(dirpath, second_file_filename)
            with open(second_file_path, 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            # Call command
            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none'}
            call_command('feed', *args, **opts)

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[1].filename, second_file_filename)

            # Suddenly a file disappears
            os.remove(first_file_path)

            # Call command again with prune option
            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none', 'prune': True}
            call_command('feed', *args, **opts)

            # Only second file in database
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, second_file_filename)

    def test_feed_command_with_lyrics(self):
        """
        Test feed command with lyrics extracted from ass file
        """
        # Pre-Assertions
        songs = Song.objects.all()
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            media_file_filename = "The file.mp4"
            with open(os.path.join(dirpath, media_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            subtitle_file_filename = "The file.ass"
            subtitle_file_filepath_origin = os.path.join(
                    APP_DIR,
                    RESSOURCES_DIR,
                    SUBTITLES_DIR,
                    'simple.ass'
                    )

            shutil.copy(subtitle_file_filepath_origin,
                    os.path.join(dirpath, subtitle_file_filename))

            # Call command
            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none'}
            call_command('feed', *args, **opts)

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, media_file_filename)

            # Check against expected file
            with open(subtitle_file_filepath_origin + "_expected") as expected:
                expected_lyrics_lines = expected.read().splitlines()
                self.assertEqual(songs[0].lyrics.splitlines(), expected_lyrics_lines)

    def test_feed_command_with_lyrics_txt(self):
        """
        Test feed command with lyrics extract from text file
        """
        # Pre-Assertions
        songs = Song.objects.all()
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            media_file_filename = "The file.mp4"
            with open(os.path.join(dirpath, media_file_filename), 'wt') as f:
                f.write("This is supposed to be an mp4 file content")

            lyrics = "lalalalalala\nlunlunlun"
            subtitle_file_filename = "The file.txt"
            with open(os.path.join(dirpath, subtitle_file_filename), 'wt') as f:
                f.write(lyrics)

            # Call command
            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none'}
            call_command('feed', *args, **opts)

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, media_file_filename)
            self.assertEqual(songs[0].lyrics.splitlines(), lyrics.splitlines())

    @unittest.skipUnless(
            FFmpegWrapper.is_available(),
            "FFmpeg is not available."
            )
    def test_feed_command_with_lyrics_embedded(self):
        """
        Test feed command with lyrics embedded into a media file
        """
        # Pre-Assertions
        songs = Song.objects.all()
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            media_file_filename = "The file.mkv"
            media_file_filepath_origin = os.path.join(
                    APP_DIR,
                    RESSOURCES_DIR,
                    'lyrics_embedded.mkv'
                    )

            shutil.copy(media_file_filepath_origin,
                    os.path.join(dirpath, media_file_filename))

            # Call command
            args = [dirpath]
            opts = {'quiet': True, 'metadata_parser': 'none'}
            call_command('feed', *args, **opts)

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, media_file_filename)

            # Check against expected file
            with open(media_file_filepath_origin + "_expected") as expected:
                expected_lyrics_lines = expected.read().splitlines()
                self.assertEqual(songs[0].lyrics.splitlines(), expected_lyrics_lines)
