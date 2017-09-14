import tempfile
from django.core.management import call_command
from django.test import TestCase
from .models import WorkType, SongTag

class QueryLanguageParserTestCase(TestCase):

    def setUp(self):
        # Create work types
        self.wt1 = WorkType(name="WorkType1", query_name="wt1")
        self.wt1.save()
        self.wt2 = WorkType(name="WorkType2", query_name="wt2")
        self.wt2.save()

    def test_createTags_command(self):
        """
        Test create tags command
        """
        # Pre-Assertions
        tags = SongTag.objects.all().order_by('name')
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
