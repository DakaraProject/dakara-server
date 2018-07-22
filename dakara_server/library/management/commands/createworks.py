import os
import sys
import logging
import importlib

from django.core.management.base import BaseCommand, CommandError

from library.models import (WorkType, WorkAlternativeTitle, Work)

from .feed_components import default_work_parser

# get logger
logger = logging.getLogger(__name__)


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
        self.work_file = work_file
        self.parser = parser

    @staticmethod
    def check_parser_result(dict_work, work_title=None):
        """Check if a work is correctly structured

        Return
            True if the work dictionnary is correctly structured
        """
        field_names = ('subtitle', 'alternative_titles')

        if not isinstance(dict_work, dict):
            logger.warning((
                "Value associated to key work {} "
                "should be a dictionnary".format(work_title)))
            return False

        has_correct_struct = True
        for field in dict_work:
            if field not in field_names:
                has_correct_struct = False
                if work_title:
                    logger.warning(
                        "Incorrect field '{}' for '{}'.".format(
                            field,
                            work_title))
                else:
                    logger.warning(
                        "Incorrect field '{}'".format(field))

        return has_correct_struct

    def creatework(self, work_type_entry, work_title, dict_work):
        """Create or update a work in database."""
        # get or create work
        work_entry, work_created = Work.objects.get_or_create(
            title__iexact=work_title,
            work_type__id=work_type_entry.id,
            defaults={
                'title': work_title,
                'work_type': work_type_entry}
            )

        if work_created:
            logger.debug("Created work '{}'.".format(work_title))

        # get subtitle
        if 'subtitle' in dict_work:
            work_entry.subtitle = dict_work['subtitle']

        # get work alternative titles or create them
        if 'alternative_titles' in dict_work:
            for alt_title in dict_work['alternative_titles']:
                self.create_alternative_title(
                        work_entry,
                        work_title,
                        alt_title)

        # save work in the database
        work_entry.save()

    def create_alternative_title(self, work_entry, work_title, alt_title):
        _, work_alt_title_created = WorkAlternativeTitle.objects.get_or_create(
                title__iexact=alt_title,
                work__title__iexact=work_title,
                defaults={
                    'title': alt_title,
                    'work': work_entry}
                )

        if work_alt_title_created:
            logger.debug("Created alternative titles '{}' for '{}'.".format(
                alt_title, work_title))

    def createworks(self):
        """Create or update works provided."""
        # parse the work file to get the data structure
        try:
            works = self.parser.parse_work(self.work_file)
        except BaseException as exc:
            raise CommandError("{}".format(str(exc))) from exc

        work_success = True
        # get works or create it
        for worktype_query_name, dict_work_type in works.items():

            logger.debug("Get work type '{}'".format(worktype_query_name))
            # get work type
            try:
                work_type_entry = WorkType.objects.get(
                        query_name__iexact=worktype_query_name
                        )

                # get work titles and their attributes
                for work_title, dict_work in dict_work_type.items():

                    if dict_work is None:
                        # create an empty dictionnary in the case only
                        # the title has been provided
                        dict_work = {}
                    # check that the work data is well structured
                    elif not self.check_parser_result(
                            dict_work, work_title=work_title):
                        logger.debug(
                            "Ignore work '{}' creation or update.".format(
                                work_title))
                        continue

                    self.creatework(work_type_entry, work_title, dict_work)

            except WorkType.DoesNotExist:
                work_success = False
                logger.error((
                    "Unable to find work type query name '{}'. Use "
                    "createworktypes command first to create "
                    "work types.".format(worktype_query_name)))

        if work_success:
            logger.info("Works successfully created.")


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
            "-d",
            "--debug",
            help="Display debug messages.",
            action="store_true"
        )

    def handle(self, *args, **options):
        """Process the feeding
        """
        # work file data
        work_file = os.path.join(
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

        # debug
        if options.get('debug'):
            logger.setLevel(logging.DEBUG)

        work_creator = WorkCreator(
                work_file,
                parser)

        # run the work creator
        work_creator.createworks()
