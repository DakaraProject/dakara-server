from tempfile import NamedTemporaryFile
from django.core.management import call_command
from django.test import TestCase
from .models import SongTag

class CreatetagsCommandTestCase(TestCase):

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
