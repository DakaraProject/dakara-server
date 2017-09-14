import tempfile
from django.core.management import call_command
from django.test import TestCase
from .models import WorkType, SongTag

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
        config_file = tempfile.NamedTemporaryFile(mode='wt')
        config_file.write(file_content)
        config_file.flush()

        # Call command
        args = [config_file.name]
        opts = {}
        call_command('createtags', *args, **opts)

        # Post-Assertions
        tags = SongTag.objects.all().order_by('name')
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
        work_types = WorkType.objects.all().order_by('query_name')
        self.assertEqual(len(work_types), 0)

        file_content = """worktypes:
  - query_name: work-type-one
    name: Work type one
    icon_name: elephant
  - query_name: work-type-two
    name: Work type two
    icon_name: cat"""

        # Create temporary config file
        config_file = tempfile.NamedTemporaryFile(mode='wt')
        config_file.write(file_content)
        config_file.flush()

        # Call command
        args = [config_file.name]
        opts = {}
        call_command('createworktypes', *args, **opts)

        # Post-Assertions
        work_types = WorkType.objects.all().order_by('query_name')
        self.assertEqual(len(work_types), 2)
        self.assertEqual(work_types[0].query_name, "work-type-one")
        self.assertEqual(work_types[0].name, "Work type one")
        self.assertEqual(work_types[0].icon_name, "elephant")
        self.assertEqual(work_types[1].query_name, "work-type-two")
        self.assertEqual(work_types[1].name, "Work type two")
        self.assertEqual(work_types[1].icon_name, "cat")
