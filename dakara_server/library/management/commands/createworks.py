import os
import sys
import logging
import importlib

import progressbar
from django.core.management.base import BaseCommand

from library.models import (WorkType, WorkAlternativeTitle, Work)

from .feed_components import default_work_parser
# from .feed_components.progress_bar import TextProgressBar, TextNullBar

# TODO set the progress bar (?)

# wrap a special stream for warnings
#
# The wrapping done by progressbar seems to reassign the ouput and flush it
# when needed, and not automatically. If the standard error is wrapped, it
# mutes any exception, which is not acceptable. So, we create a custom wrapped
# stream and assign warnings to use it since we cannot specify a new stream, we
# use stderr for that, and reassign it to its origineal value right after.
origin_stderr = sys.stderr
wrapped_stderr = progressbar.streams.wrap_stderr()
sys.stderr = origin_stderr

# get logger
logger = logging.getLogger(__name__)

# hack the logger handler to use the wrapped stderr
if logger.handlers:
    logger.handlers[0].stream = wrapped_stderr


class WorkCreator:
    """Work creator and updater. Create and update works in the
    database provided a work file and a parser.

    Args:
        work_file (str): Path of the file storing the works data.
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
            parser,
            dry_run=False):
        self.dry_run = dry_run
        # get works data
        self.works = parser.parse_work(work_file)
        self.work_alt_title_listing = []

    # TODO restrict search fields
    @staticmethod
    def check_parser_result(dict_work):
        """Check if a work is correctly structured
        """
        field_error = None
        for field in dict_work:
            if field not in Work._meta.fields:
                field_error = field
                break

        return field_error

    def save(self, obj):
        """Save an object in database depending of the options."""
        if self.dry_run:
            obj.show(sys.stdout)
        else:
            obj.save()

    def creatework(self, query_name, title_work, dict_work):
        """Create or update a work in database."""
        # check that the work data is well structured
        field_error = self.check_parser_result(dict_work)
        if field_error is not None:
            logger.warning(
                "Incorrect field '{}' for '{}'".format(
                    field_error,
                    title_work))
            return

        work_entry, work_created = Work.objects.get_or_create(
            work__title__iexact=title_work
        )

        if work_created:
            logger.debug("Created work '{}'".format(title_work))

        # get title
        work_entry.title = title_work

        # get subtitle
        if dict_work['subtitle']:
            work_entry.subtitle = dict_work['subtitle']

        # get work type
        try:
            work_type_entry = WorkType.objects.get(
                query_name=query_name
            )

            work_entry.work_type = work_type_entry

        except WorkType.DoesNotExist:
            logger.warning("""Unable to find work type query name '{}'.
                            Use createworktypes command first to create \
                                    work types.""".format(query_name))

        # get work alternative titles or create them
        self.work_alt_title_listing = []
        for alt_title in dict_work['alternative_titles']:
            self.create_alternative_title(title_work, alt_title)

            if self.work_alt_title_listing:
                logger.debug("Created alternative titles '{}' for '{}'".format(
                        "', '".join(self.work_alt_title_listing), title_work))

        # save work in the database
        self.save(work_entry)

    def create_alternative_title(self, title_work, alt_title):
        work_alt_title_entry, work_alt_title_created = WorkAlternativeTitle.get_or_create(  # noqa E501
            title__iexact=alt_title,
            work__title__iexact=title_work
            )

        work_alt_title_entry.title = alt_title
        work_alt_title_entry.work = title_work

        # save work alternative title in the database
        self.save(work_alt_title_entry)

        if work_alt_title_created:
            self.work_alt_title_listing.append(alt_title)

    def createworks(self):
        """Create or update works provided."""
        # get works or create it
        for query_name, dict_work_type in self.works:
            for title_work, dict_work in dict_work_type:
                self.creatework(query_name, title_work, dict_work)

        logger.debug("Works successfully created.")


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

        parser.add_argument(
            "-r",
            "--dry-run",
            help="Run script in test mode, don't save anything in database.",
            action="store_true"
        )

    def handle(self, *args, **options):
        """Process the feeding
        """
        # work file data
        work_file = os.path.normpath(options['work-file'])

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
                parser,
                dry_run=options.get('dry_run'))

        # run the work creator
        work_creator.createworks()
