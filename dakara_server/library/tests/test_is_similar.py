import os
import csv

from django.test import TestCase

from library.management.commands.feed_components.utils import is_similar

RESSOURCES_DIR = "tests_ressources"
APP_DIR = os.path.dirname(os.path.abspath(__file__))


class IsSimilarTestCase(TestCase):
    def test_is_similar_from_file(self):
        """Rum similarity tests among several strings
        """
        # load test data
        file_path = os.path.join(APP_DIR, RESSOURCES_DIR, "is_similar.csv")
        with open(file_path, "r") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=";")
            for row in reader:
                ratio = is_similar(row["string1"], row["string2"])
                expected_similar = bool(int(row["similar"]))
                self.assertEqual(
                    bool(ratio),
                    expected_similar,
                    "{} and {} should {}be similar".format(
                        row["string1"],
                        row["string2"],
                        "" if expected_similar else "not ",
                    ),
                )
