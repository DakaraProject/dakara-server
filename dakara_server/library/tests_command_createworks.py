import os

from django.core.management import call_command
from django.core.management.base import CommandError

from django.test import TestCase
from .models import WorkType, Work

APP_DIR = os.path.dirname(os.path.abspath(__file__))
RESSOURCES_DIR = os.path.join('tests_ressources', 'work_files')
DIR_WORK_FILES = os.path.join(APP_DIR, RESSOURCES_DIR)


class CommandsTestCase(TestCase):
    def setUp(self):
        WorkType.objects.create(query_name="WorkType 1")

    def test_createworks_from_correct_work_file(self):
        """Test create works command from a correctly structured work file
        """
        # Call command
        work_file = os.path.join(
                DIR_WORK_FILES,
                'correct_work_file.json')

        args = [work_file]
        opts = {'verbosity': 0}
        call_command('createworks', *args, **opts)

        # Work assertions
        works = Work.objects.order_by('title')

        self.assertEqual(len(works), 3)

        self.assertEqual(works[0].title, "Work 1")
        self.assertEqual(works[0].subtitle, "Subtitle 1")
        self.assertEqual(works[0].work_type.query_name, "WorkType 1")
        self.assertCountEqual(
            [alt.title for alt in works[0].alternative_titles.all()],
            ["AltTitle 1", "AltTitle 2"])

        self.assertEqual(works[1].title, "Work 2")
        self.assertEqual(works[1].subtitle, "Subtitle 2")
        self.assertEqual(works[1].work_type.query_name, "WorkType 1")
        self.assertCountEqual(
            [alt.title for alt in works[1].alternative_titles.all()], [])

        self.assertEqual(works[2].title, "Work 3")
        self.assertEqual(works[2].subtitle, "")
        self.assertEqual(works[2].work_type.query_name, "WorkType 1")
        self.assertCountEqual(
            [alt.title for alt in works[2].alternative_titles.all()],
            ["AltTitle 1", "AltTitle 3"])

    def test_createworks_with_incorrect_work_title(self):
        """Create works from a work where the title is incorrect."""
        # Call command
        work_file = os.path.join(
                DIR_WORK_FILES,
                'title_error_work_file.json')

        args = [work_file]
        opts = {'verbosity': 0}
        call_command('createworks', *args, **opts)

        # Work assertions
        works = Work.objects.order_by('title')

        self.assertEqual(len(works), 0)

    def test_createworks_with_work_type_error(self):
        """Create works from a work which work type does not exist."""
        # Call command
        work_file = os.path.join(
                DIR_WORK_FILES,
                'work_type_error_work_file.json')

        args = [work_file]
        opts = {'verbosity': 0}
        call_command('createworks', *args, **opts)

        # Work assertion
        self.assertEqual(Work.objects.count(), 0)

    def test_createworks_with_work_title_missing(self):
        """Create works from a work where the title is missing."""
        # Call command
        work_file = os.path.join(
                DIR_WORK_FILES,
                'title_missing_work_file.json')

        args = [work_file]
        opts = {'verbosity': 0}
        call_command('createworks', *args, **opts)

        # Work assertion
        self.assertEqual(Work.objects.count(), 0)

    def test_createworks_with_different_subtitle(self):
        """Create two works with the same title but different subtitle."""
        # Call command
        work_file = os.path.join(
                DIR_WORK_FILES,
                'different_subtitle_work_file.json')

        args = [work_file]
        opts = {'verbosity': 0}
        call_command('createworks', *args, **opts)

        # Work assertion
        works = Work.objects.order_by('title', 'subtitle')

        self.assertEqual(len(works), 2)

        self.assertEqual(works[0].title, "Work 1")
        self.assertEqual(works[0].subtitle, "Subtitle 1")

        self.assertEqual(works[1].title, "Work 1")
        self.assertEqual(works[1].subtitle, "Subtitle 2")

    def test_createworks_with_work_type_without_work_list(self):
        """Check there is no work created when work type value is not a list"""
        # Create work type
        WorkType.objects.create(query_name="WorkType 2")

        # Call command
        work_file = os.path.join(
                DIR_WORK_FILES,
                'work_type_without_work_list_work_file.json')

        args = [work_file]
        opts = {'verbosity': 0}
        call_command('createworks', *args, **opts)

        self.assertEqual(Work.objects.count(), 0)

    def test_createworks_with_nonexistent_file(self):
        """Check the command raises an error with a nonexistent file."""
        work_file = os.path.join(
                DIR_WORK_FILES,
                'this_file_does_not_exist.json')

        with self.assertRaises(CommandError):
            # Call command
            args = [work_file]
            opts = {'verbosity': 0}
            call_command('createworks', *args, **opts)
