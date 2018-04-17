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

    def test_createworktypes_command_prune(self):
        """
        Test create work types command with existing work types and prune
        option
        """
        # Create existing work types

        # This work type exist in config file
        # Its name and icon name will be updated by the command
        work_type_one = WorkType()
        work_type_one.query_name = "work-type-one"
        work_type_one.name = "Old name"
        work_type_one.save()
        # This work type does not exists in config file,
        # Will be removed
        work_type_two = WorkType()
        work_type_two.query_name = "work-type-wrong"
        work_type_two.name = "Should not exist anymore"
        work_type_two.save()

        # Pre-Assertions
        work_types = WorkType.objects.order_by('query_name')
        self.assertEqual(len(work_types), 2)
        self.assertEqual(work_types[0].query_name, "work-type-one")
        self.assertEqual(work_types[1].query_name, "work-type-wrong")

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
            opts = {'quiet': True, 'prune': True}
            call_command('createworktypes', *args, **opts)

            # Post-Assertions
            work_types = WorkType.objects.order_by('query_name')

            # Only the two work types from config file
            self.assertEqual(len(work_types), 2)
            # Work type one, has been updated, but has kept his id
            self.assertEqual(work_types[0].query_name, "work-type-one")
            self.assertEqual(work_types[0].id, work_type_one.id)
            self.assertEqual(work_types[0].name, "Work type one")
            self.assertEqual(work_types[0].name_plural, "Work type one plural")
            self.assertEqual(work_types[0].icon_name, "elephant")
            # Work type two has been created
            self.assertEqual(work_types[1].query_name, "work-type-two")
            self.assertEqual(work_types[1].name, "Work type two")
            self.assertEqual(work_types[1].name_plural, "Work type two plural")
            self.assertEqual(work_types[1].icon_name, "cat")
