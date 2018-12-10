from tempfile import TemporaryDirectory
import os
import shutil
import unittest

from django.core.management import call_command
from django.test import TestCase

from .models import Song
from .management.commands.feed_components.ffmpeg_wrapper import FFmpegWrapper

RESSOURCES_DIR = "tests_ressources"
SUBTITLES_DIR = "subtitles"
APP_DIR = os.path.dirname(os.path.abspath(__file__))


class FeedCommandTestCase(TestCase):
    def call_feed_command(self, directory_path, options={}):
        args = [directory_path]
        opts = {'quiet': True, 'metadata_parser': 'none'}
        opts.update(options)

        call_command('feed', *args, **opts)

    @staticmethod
    def create_media_file(path, filename):
        """Create file in path
        returns path to file
        """
        filepath = os.path.join(path, filename)
        with open(filepath, 'wt') as file:
            file.write("This is supposed to be an mp4 file content")

        return filepath

    def test_feed_command(self):
        """Test feed command
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            first_file_filename = "The first file.mp4"
            self.create_media_file(dirpath, first_file_filename)

            second_file_filename = "The second file.mp4"
            self.create_media_file(dirpath, second_file_filename)

            # Call command
            self.call_feed_command(dirpath)

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, '')
            self.assertEqual(songs[0].title,
                             os.path.splitext(first_file_filename)[0])
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, '')
            self.assertEqual(songs[1].title,
                             os.path.splitext(second_file_filename)[0])

    def test_feed_command_with_trailing_slash(self):
        """Test feed command when path contains a trailling slash

        There was a bug, when a path with trailing slash was given,
        The directory field was empty instead of containing the containing
        folder name.
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            first_file_filename = "The first file.mp4"
            self.create_media_file(dirpath, first_file_filename)

            second_file_filename = "The second file.mp4"
            self.create_media_file(dirpath, second_file_filename)

            # Call command
            # Join with empty string to add a trailing slash if it's not
            # already there
            self.call_feed_command(os.path.join(dirpath, ''))

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[0].directory, '')
            self.assertEqual(songs[0].title,
                             os.path.splitext(first_file_filename)[0])
            self.assertEqual(songs[1].filename, second_file_filename)
            self.assertEqual(songs[1].directory, '')
            self.assertEqual(songs[1].title,
                             os.path.splitext(second_file_filename)[0])

    def test_feed_command_with_parser(self):
        """Test feed command with parser
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            first_file_filename = (
                "The first song name - First artist name - First work title "
                "- FIRSTTAG.mp4"
            )
            self.create_media_file(dirpath, first_file_filename)

            second_file_filename = (
                "The second song name - Second artist name - Second work "
                "title - SECONDTAG.mp4"
            )
            self.create_media_file(dirpath, second_file_filename)

            # Call command
            self.call_feed_command(dirpath,
                                   {'parser': "library/parser_test.py"})

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            first_song = songs[0]
            second_song = songs[1]

            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, '')
            self.assertEqual(first_song.title, "The first song name")
            # check artist
            self.assertEqual(len(first_song.artists.all()), 1)
            self.assertEqual(
                first_song.artists.all()[0].name,
                "First artist name")
            # check work
            self.assertEqual(len(first_song.works.all()), 1)
            self.assertEqual(
                first_song.works.all()[0].title,
                "First work title")
            # check tag
            self.assertEqual(len(first_song.tags.all()), 1)
            self.assertEqual(first_song.tags.all()[0].name, "FIRSTTAG")

            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, '')
            self.assertEqual(second_song.title, "The second song name")
            # check artist
            self.assertEqual(len(second_song.artists.all()), 1)
            self.assertEqual(
                second_song.artists.all()[0].name,
                "Second artist name")
            # check work
            self.assertEqual(len(second_song.works.all()), 1)
            self.assertEqual(
                second_song.works.all()[0].title,
                "Second work title")
            # check tag
            self.assertEqual(len(second_song.tags.all()), 1)
            self.assertEqual(second_song.tags.all()[0].name, "SECONDTAG")

    def test_feed_command_rename(self):
        """Test feed command when a file has been renamed
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            # create the first file
            first_file_filename = "The first file.mp4"
            first_file_filepath = self.create_media_file(
                dirpath, first_file_filename)

            # create the second file
            second_file_filename = "The second file.mp4"
            self.create_media_file(dirpath, second_file_filename)

            # call command first to populate
            self.call_feed_command(dirpath)

            # 2 files should exist
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            first_song = songs[0]
            second_song = songs[1]

            # check the databases entries are conform with the files
            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, '')
            self.assertEqual(first_song.title,
                             os.path.splitext(first_file_filename)[0])
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, '')
            self.assertEqual(second_song.title,
                             os.path.splitext(second_file_filename)[0])

            # suddenly, rename the first file
            first_file_filename_new = "The first new file.mp4"
            first_file_filepath_new = os.path.join(
                dirpath, first_file_filename_new)
            os.rename(first_file_filepath, first_file_filepath_new)

            # call command first to populate
            self.call_feed_command(dirpath)

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
        """Test feed command when a file has been completely renamed
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            # create the first file
            first_file_filename = "The first file.mp4"
            first_file_filepath = self.create_media_file(
                dirpath, first_file_filename)

            # create the second file
            second_file_filename = "The second file.mp4"
            self.create_media_file(dirpath, second_file_filename)

            # Call command first to populate
            self.call_feed_command(dirpath)

            # basic test: the two files are in database as expected
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            first_song = songs[0]
            second_song = songs[1]
            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, '')
            self.assertEqual(first_song.title,
                             os.path.splitext(first_file_filename)[0])
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, '')
            self.assertEqual(second_song.title,
                             os.path.splitext(second_file_filename)[0])

            # now, rename the first file
            first_file_filename_new = "Something completely different.mp4"
            first_file_filepath_new = os.path.join(
                dirpath, first_file_filename_new)
            os.rename(first_file_filepath, first_file_filepath_new)

            # call command first to populate
            self.call_feed_command(dirpath)

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
        """Test feed command
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
            first_file_filepath = self.create_media_file(
                os.path.join(dirpath, first_directory),
                first_file_filename
            )

            second_file_filename = "The second file.mp4"
            self.create_media_file(
                os.path.join(dirpath, first_directory),
                second_file_filename
            )

            # create 1 file in second directory
            third_file_filename = "The third file.mp4"
            self.create_media_file(
                os.path.join(dirpath, second_directory),
                third_file_filename
            )

            # call command on each subdirectories
            self.call_feed_command(dirpath, {'directory': first_directory})
            self.call_feed_command(dirpath, {'directory': second_directory})

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
            self.call_feed_command(dirpath, {'directory': first_directory})
            self.call_feed_command(dirpath, {'directory': second_directory})

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
        """Test feed command file renamed and new file similar name

        Test feed command when a file has been renamed
        and a new file simillar name is added.
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            # create the first file
            first_file_filename = "The first file.mp4"
            first_file_filepath = self.create_media_file(
                dirpath, first_file_filename)

            # create the second file
            second_file_filename = "The second file.mp4"
            self.create_media_file(dirpath, second_file_filename)

            # call command first to populate
            self.call_feed_command(dirpath)

            # 2 files should exist
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            first_song = songs[0]
            second_song = songs[1]

            # check the databases entries are conform with the files
            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, '')
            self.assertEqual(first_song.title,
                             os.path.splitext(first_file_filename)[0])
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, '')
            self.assertEqual(second_song.title,
                             os.path.splitext(second_file_filename)[0])

            # suddenly, rename the first file
            first_file_filename_new = "The first new file.mp4"
            first_file_filepath_new = os.path.join(
                dirpath, first_file_filename_new)
            os.rename(first_file_filepath, first_file_filepath_new)

            # create new file with similar name
            third_file_filename = "The zew first file.mp4"
            self.create_media_file(dirpath, third_file_filename)

            # call command again to populate
            self.call_feed_command(dirpath)

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
            self.assertTrue(
                first_song.id == first_song_new.id or
                first_song.id == third_song_new.id
            )

    def test_feed_command_prune(self):
        """Test feed command with prune argument
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            # create the first file
            first_file_filename = "The first file.mp4"
            first_file_filepath = self.create_media_file(
                dirpath, first_file_filename)

            # create the second file
            second_file_filename = "The second file.mp4"
            self.create_media_file(dirpath, second_file_filename)

            # Call command
            self.call_feed_command(dirpath)

            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            self.assertEqual(songs[0].filename, first_file_filename)
            self.assertEqual(songs[1].filename, second_file_filename)

            # Suddenly a file disappears
            os.remove(first_file_filepath)

            # Call command again with prune option
            self.call_feed_command(dirpath, {'prune': True})

            # Only second file in database
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, second_file_filename)

    def test_feed_command_with_lyrics(self):
        """Test feed command with lyrics extracted from ass file
        """
        # Pre-Assertions
        songs = Song.objects.all()
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            media_file_filename = "The file.mp4"
            self.create_media_file(dirpath, media_file_filename)

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
            self.call_feed_command(dirpath)

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, media_file_filename)

            # Check against expected file
            with open(subtitle_file_filepath_origin + "_expected") as expected:
                expected_lyrics_lines = expected.read().splitlines()
                self.assertEqual(
                    songs[0].lyrics.splitlines(),
                    expected_lyrics_lines)

    def test_feed_command_with_lyrics_txt(self):
        """Test feed command with lyrics extract from text file
        """
        # Pre-Assertions
        songs = Song.objects.all()
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            media_file_filename = "The file.mp4"
            self.create_media_file(dirpath, media_file_filename)

            lyrics = "lalalalalala\nlunlunlun"
            subtitle_file_filename = "The file.txt"
            with open(os.path.join(dirpath, subtitle_file_filename),
                      'wt') as file:
                file.write(lyrics)

            # Call command
            self.call_feed_command(dirpath)

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, media_file_filename)
            self.assertEqual(songs[0].lyrics.splitlines(), lyrics.splitlines())

    @unittest.skipUnless(
        FFmpegWrapper.is_available(),
        "FFmpeg is not available."
    )
    def test_feed_command_with_lyrics_embedded(self):
        """Test feed command with lyrics embedded into a media file
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
            self.call_feed_command(dirpath)

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            self.assertEqual(songs[0].filename, media_file_filename)

            # Check against expected file
            with open(media_file_filepath_origin + "_expected") as expected:
                expected_lyrics_lines = expected.read().splitlines()
                self.assertEqual(
                    songs[0].lyrics.splitlines(),
                    expected_lyrics_lines)

    def test_feed_command_rename_multiple(self):
        """Test feed command when multiple files has been renamed
        """
        # Pre-Assertions
        songs = Song.objects.order_by('title')
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:
            # create the first file
            first_file_filename = "The first file.mp4"
            first_file_filepath = self.create_media_file(
                dirpath, first_file_filename)

            # create the second file
            second_file_filename = "The second file.mp4"
            second_file_filepath = self.create_media_file(
                dirpath, second_file_filename)

            # call command first to populate
            self.call_feed_command(dirpath)

            # 2 files should exist
            songs = Song.objects.order_by('title')
            self.assertEqual(len(songs), 2)
            first_song = songs[0]
            second_song = songs[1]

            # check the databases entries are conform with the files
            self.assertEqual(first_song.filename, first_file_filename)
            self.assertEqual(first_song.directory, '')
            self.assertEqual(first_song.title,
                             os.path.splitext(first_file_filename)[0])
            self.assertEqual(second_song.filename, second_file_filename)
            self.assertEqual(second_song.directory, '')
            self.assertEqual(second_song.title,
                             os.path.splitext(second_file_filename)[0])

            # suddenly, rename the first and second files
            first_file_filename_new = "The first new file.mp4"
            first_file_filepath_new = os.path.join(
                dirpath, first_file_filename_new)
            os.rename(first_file_filepath, first_file_filepath_new)

            second_file_filename_new = "The second new file.mp4"
            second_file_filepath_new = os.path.join(
                dirpath, second_file_filename_new)
            os.rename(second_file_filepath, second_file_filepath_new)

            # call command to update database
            self.call_feed_command(dirpath)

            # there should be still 2 entries in the database
            # since the filenames are close to the original filenames
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

            # check new second file, which is the same as initial second file
            # the identity is checked by ID
            self.assertEqual(second_song_new.id, second_song.id)
            self.assertEqual(
                second_song_new.filename,
                second_file_filename_new)
            self.assertEqual(second_song_new.directory, '')
            self.assertEqual(second_song_new.title,
                             os.path.splitext(second_file_filename_new)[0])

    def test_feed_command_artist_work_tag_change(self):
        """Test feed command when a song is updated

        The song has a different artist, work and tag.
        """
        # Pre-Assertions
        songs = Song.objects.all()
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:

            # Create a file to be feed
            filename = "The song name - Artist name - Work title - TAG.mp4"
            filepath = self.create_media_file(dirpath, filename)

            # Call command
            self.call_feed_command(dirpath,
                                   {'parser': "library/parser_test.py"})

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            song = songs[0]
            self.assertEqual(song.filename, filename)
            # Check artist
            self.assertEqual(len(song.artists.all()), 1)
            self.assertEqual(song.artists.all()[0].name, "Artist name")
            # Check work
            self.assertEqual(len(song.works.all()), 1)
            self.assertEqual(song.works.all()[0].title, "Work title")
            # Check tag
            self.assertEqual(len(song.tags.all()), 1)
            self.assertEqual(song.tags.all()[0].name, "TAG")

            # The file is renamed with a different artist name
            filename_new = (
                "The song name - New artist name - New work title - "
                "NEWTAG.mp4"
            )
            filepath_new = os.path.join(dirpath, filename_new)
            os.rename(filepath, filepath_new)

            # Call command again
            self.call_feed_command(dirpath,
                                   {'parser': "library/parser_test.py"})

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            song_new = songs[0]
            # Same song
            self.assertEqual(song_new.id, song.id)
            # New artist
            self.assertEqual(len(song_new.artists.all()), 1)
            self.assertEqual(song_new.artists.all()[0].name, "New artist name")
            # New work
            self.assertEqual(len(song_new.works.all()), 1)
            self.assertEqual(song_new.works.all()[0].title, "New work title")
            # New tag
            self.assertEqual(len(song_new.tags.all()), 1)
            self.assertEqual(song_new.tags.all()[0].name, "NEWTAG")

    def test_feed_command_no_work_type(self):
        """Test feed command when parser return work but not worktype
           Work should not be created, because a work can not exists
           without worktype
        """
        # Pre-Assertions
        songs = Song.objects.all()
        self.assertEqual(len(songs), 0)

        with TemporaryDirectory(prefix="dakara.") as dirpath:

            # Create a file to be feed
            filename = "The song name - Artist name - Work title - TAG.mp4"
            self.create_media_file(dirpath, filename)

            # Call command with parser returning work, but no work type
            self.call_feed_command(dirpath,
                                   {'parser':
                                    "library/parser_test_no_work_type.py"})

            songs = Song.objects.all()
            self.assertEqual(len(songs), 1)
            song = songs[0]
            self.assertEqual(song.filename, filename)
            # Check artist
            self.assertEqual(len(song.artists.all()), 1)
            self.assertEqual(song.artists.all()[0].name, "Artist name")
            # Check work was not created
            self.assertEqual(len(song.works.all()), 0)
            # Check tag
            self.assertEqual(len(song.tags.all()), 1)
            self.assertEqual(song.tags.all()[0].name, "TAG")
