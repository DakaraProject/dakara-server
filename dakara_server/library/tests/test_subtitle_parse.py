import os

from django.test import TestCase

from library.management.commands.feed_components.subtitle_parser import (
    Pysubs2SubtitleParser,
)

RESSOURCES_DIR = os.path.join("tests_ressources", "subtitles")
APP_DIR = os.path.dirname(os.path.abspath(__file__))


class ASSParserTestCase(TestCase):
    def test_subtitles_from_files(self):
        """Run lyrics extraction test on several files

        For each subtitle file in ressource directory, open and extract lyrics
        from the file, and test that the result is the same as the
        corresponding file with "_expected" prefix.

        This method is called from tests methods.
        """
        directory = os.path.join(APP_DIR, RESSOURCES_DIR)
        for file_name in os.listdir(directory):
            if not file_name.endswith(".ass"):
                continue

            file_path = os.path.join(directory, file_name)

            parser = Pysubs2SubtitleParser(file_path)
            lyrics = parser.get_lyrics()
            lines = lyrics.splitlines()

            # Check against expected file
            with open(file_path + "_expected") as expected:
                expected_lines = expected.read().splitlines()

            self.assertEqual(lines, expected_lines, "In file: {}".format(file_name))
