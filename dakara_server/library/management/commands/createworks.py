import os
import sys
import logging
import importlib

from django.core.management.base import BaseCommand

from library.models import (WorkType, WorkAlternativeTitle, Work)

from .feed_components import default_work_parser

# get logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

logger.addHandler(handler)


class WorkCreator:
    """Work creator and updater. Create and update works in the
    database provided a work file and a parser.

    Args:
        work_file (str): Absolute path of the file storing the works data.
        parser (module): Custom python module used to extract data from file.
        dry_run (bool): Run script in test mode.

    About parser:
        This module should define a method called `parse_work` which takes
        a file path as argument and return a dictionnary with the following:
            works (dict): keys are a query name worktype, values are
            dictionnary such that:
                keys are title of a work associated to the worktype, values are
                the following:
                    subtitle (str): subtitle of a work
                    alternative_titles (list): list of alternative names of
                    a work
    """
    def __init__(
            self,
            work_file,
            parser):
        self.works = parser.parse_work(work_file)
        self.work_alt_title_listing = []

    @staticmethod
    def check_parser_result(dict_work):
        """Check if a work is correctly structured

        Return
            None if the structure, otherwise the field not recognized.
        """
        field_names = ('subtitle', 'alternative_titles')

        has_correct_struct = True
        field_error = None
        for field in dict_work:
            if field not in field_names:
                has_correct_struct = False
                field_error = field
                break

        return has_correct_struct, field_error

    def creatework(self, work_type_entry, work_title, dict_work):
        """Create or update a work in database."""
        # check that the work data is well structured
        has_correct_struct, field_error = self.check_parser_result(dict_work)
        if not has_correct_struct:
            logger.warning(
                "Incorrect field '{}' for '{}'".format(
                    field_error,
                    work_title))
            return

        work_entry, work_created = Work.objects.get_or_create(
            title__iexact=work_title
        )

        if work_created:
            logger.info("Created work '{}'.".format(work_title))

        # get title
        work_entry.title = work_title

        # get work type
        work_entry.work_type = work_type_entry

        # get subtitle
        if dict_work['subtitle']:
            work_entry.subtitle = dict_work['subtitle']

        # get work alternative titles or create them
        self.work_alt_title_listing = []
        for alt_title in dict_work['alternative_titles']:
            self.create_alternative_title(work_entry, work_title, alt_title)

            if self.work_alt_title_listing:
                logger.info("Created alternative titles '{}' for '{}'.".format(
                        "', '".join(self.work_alt_title_listing), work_title))

        # save work in the database
        work_entry.save()

    def create_alternative_title(self, work_entry, work_title, alt_title):
        work_alt_title_entry, work_alt_title_created = WorkAlternativeTitle.objects.get_or_create( # noqa E501
                    title=alt_title,
                    work__title=work_title,
                    defaults={'work': work_entry}
                )

        if work_alt_title_created:
            # add to the listing the alternative title created
            self.work_alt_title_listing.append(alt_title)

    def createworks(self):
        """Create or update works provided."""
        work_success = True
        # get works or create it
        for worktype_query_name, dict_work_type in self.works.items():

            # get work type
            try:
                work_type_entry = WorkType.objects.get(
                        query_name=worktype_query_name
                        )

                for work_title, dict_work in dict_work_type.items():
                    self.creatework(work_type_entry, work_title, dict_work)

            except WorkType.DoesNotExist:
                work_success = False
                logger.error("""Unable to find work type query name '{}'.
                            Use createworktypes command first to create \
                                    work types.""".format(worktype_query_name))
                continue

        if work_success:
            logger.info("Works successfully created.")
        else:
            logger.warning("An error has been detected during works creation.")


class Command(BaseCommand):
    """Command available for `manage.py` for creating works or adding
    extra information to works.
    """
    help = "Create works or add extra information to works."

    def add_arguments(self, parser):
        """Extend arguments for the command
        """
        parser.add_argument(
            "work-file",
            help="Path of the file storing the works data."
        )

        parser.add_argument(
            "--parser",
            help="""Name of a custom python module used to extract data from file name;
            see internal doc for what is expected for this module.""",
            default=None
        )

    def handle(self, *args, **options):
        """Process the feeding
        """
        # work file data
        work_file = os.path.join(
                os.getcwd(),
                os.path.normpath(options['work-file'])
                )

        # parser
        if options.get('parser'):
            parser_directory = os.path.join(
                os.getcwd(),
                os.path.dirname(options['parser'])
            )

            parser_name, _ = os.path.splitext(
                os.path.basename(options['parser']))
            sys.path.append(parser_directory)
            parser = importlib.import_module(parser_name)
        else:
            parser = default_work_parser

        work_creator = WorkCreator(
                work_file,
                parser)

        # run the work creator
        work_creator.createworks()
