from tempfile import NamedTemporaryFile
from django.core.management import call_command
from django.test import TestCase
from .models import WorkType

class CommandsTestCase(TestCase):

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

