import json

from tempfile import NamedTemporaryFile

from django.core.management import call_command
from django.test import TestCase

from .models import WorkType, WorkAlternativeTitle, Work


class CommandsTestCase(TestCase):
    def test_createworktypes_command(self):
        """Test create works command
        """
        # Create existing work type
        WorkType.objects.create(query_name="WorkType 1")

        # Pre-Assertions
        work_types = WorkType.objects.order_by('query_name')
        self.assertEqual(len(work_types), 1)

        file_content = json.dumps(
            {"WorkType 1":
             {"Work 1":
              {"subtitle": "Subtitle 1",
               "alternative_titles": [
                   "AltTitle 1",
                   "AltTitle 2"
               ]
               },
              "Work 2": {"subtitle": "Subtitle 2"},
              "Work 3":
              {"alternative_titles": [
                  "AltTitle 1",
                  "AltTitle 3",
              ]
              },
              "Work 4": None
              }
             })

        # Create temporary config file
        with NamedTemporaryFile(mode='wt', suffix=".json") as config_file:
            config_file.write(file_content)
            config_file.flush()

            # Call command
            args = [config_file.name]
            opts = {'quiet': True}
            call_command('createworks', *args, **opts)

            # Work assertions
            works = Work.objects.order_by('title')

            self.assertEqual(len(works), 4)
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

            self.assertEqual(works[3].title, "Work 4")
            self.assertEqual(works[3].subtitle, "")
            self.assertEqual(works[3].work_type.query_name, "WorkType 1")
            self.assertCountEqual(
                [alt.title for alt in works[3].alternative_titles.all()], [])

            # Work alternative title assertions
            work_alt_titles = WorkAlternativeTitle.objects.order_by(
                    'title',
                    'work__title')
            self.assertEqual(len(work_alt_titles), 4)

            self.assertEqual(work_alt_titles[0].title, "AltTitle 1")
            self.assertEqual(work_alt_titles[0].work.title, "Work 1")

            self.assertEqual(work_alt_titles[1].title, "AltTitle 1")
            self.assertEqual(work_alt_titles[1].work.title, "Work 3")

            self.assertEqual(work_alt_titles[2].title, "AltTitle 2")
            self.assertEqual(work_alt_titles[2].work.title, "Work 1")

            self.assertEqual(work_alt_titles[3].title, "AltTitle 3")
            self.assertEqual(work_alt_titles[3].work.title, "Work 3")
