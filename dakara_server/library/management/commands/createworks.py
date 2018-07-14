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


class Command(BaseCommand):
    """Command available for `manage.py` for creating works or adding
    extra information to works.

    About parser:
        This module should define a method called `parse_work` which takes
        a file path as argument and return a dictionnary with the following:
            works (dict): keys are title of a work, values are dictionnary with
            the following entries :
                subtitle (str): subtitle of a work
                work_type (str): query name of the work type of a work
                alternative_titles (list): list of alternative names of a work
    """
    help = "Create works or add extra information to works."

    def add_arguments(self, parser):
        """Extend arguments for the command
        """
        parser.add_argument(
            "work-file",
            help="File storing the works data."
        )

        parser.add_argument(
            "--parser",
            help="""Name of a custom python module used to extract data from file name;
            see internal doc for what is expected for this module.""",
            default=None
        )

    @staticmethod
    def _check_parser_result(dict_work):
        """Check if a work is correctly structured
        """
        field_error = None
        for field in dict_work:
            if field not in Work._meta.fields:
                field_error = field
                break

        return field_error

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

        # get works data
        works = parser.parse_work(work_file)

        # get works or create it
        for work in works:

            dict_work = works[work]
            # check that the work data is well structured
            field_error = self._check_parser_result(dict_work)
            if field_error is not None:
                logger.warning(
                    "Incorrect field '{}' for '{}'".format(field_error, work))
                continue

            work_entry, work_created = Work.objects.get_or_create(
                work__title__iexact=work
            )

            if work_created:
                logger.debug("Created work '{}'".format(work))

            # get title
            work_entry.title = work

            # get subtitle
            if dict_work['subtitle']:
                work_entry.subtitle = dict_work['subtitle']

            # get work type
            if dict_work['work_type']:
                try:
                    work_type_entry = WorkType.objects.get(
                        query_name=dict_work['work_type']
                    )

                    work_entry.work_type = work_type_entry
                except WorkType.DoesNotExist:
                    logger.warning("""Unable to find work type query name '{}'.
                            Use createworktypes command first to create \
                            work types.""".format(dict_work['work_type']))

            # get work alternative titles or create them
            work_alt_title_listing = []
            for alt_title in dict_work['alternative_titles']:
                work_alt_title_entry, work_alt_title_created = WorkAlternativeTitle.get_or_create( # noqa E501
                    title__iexact=alt_title,
                    work__title__iexact=work
                )

                work_alt_title_entry.title = alt_title
                work_alt_title_entry.work = work

                # save work alternative title in the database
                work_alt_title_entry.save()

                if work_alt_title_created:
                    work_alt_title_listing.append(alt_title)

            if work_alt_title_listing:
                logger.debug("Created alternative titles '{}' for '{}'".format(
                    "', '".join(work_alt_title_listing), work))

            # save work in the database
            work_entry.save()

        logger.debug("Works successfully created.")
