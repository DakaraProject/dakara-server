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
            a list such that each element of this list is a dictionnary with
            the following keys:
                    title (str): title of the work
                    subtitle (str): subtitle of the work
                    alternative_titles (list): list of alternative names of
                    a work
    """
    def __init__(
            self,
            work_file="",
            parser=None,
            debug=False,
            update_only=False):
        self.work_file = work_file
        self.parser = parser
        self.debug = debug
        self.update_only = update_only

    def remove_incorrect_works(self, work_listing):
        """Remove works that have an incorrect structure in a list of works.

        Return
            A new list with the incorrect works removed."""

        work_to_remove = []

        logger.debug("Removing the incorrect work from the current work type.")
        for index, dict_work in enumerate(work_listing):

            # check if it is a dictionary
            if not isinstance(dict_work, dict):
                work_to_remove.append(dict_work)
                logger.debug("Incorrect work at index {}: "
                             "value must be a dictionary.".format(index))
                continue

            # check if it has a title field
            work_title = dict_work.get('title')
            if not work_title:
                work_to_remove.append(dict_work)
                logger.debug("Incorrect work at index {}: "
                             "no title field found")
                continue

            logger.debug("Work '{}' is correctly structured.".format(
                    work_title))

        return [work for work in work_listing if work not in work_to_remove]

    def debug_parser_work(self, dict_work):
        """Display debug messages on a specific work dictionarry.

        Args
            dict_work: dictionnary for which the check is done
            (must have a 'title' field)
        """
        field_names = ('subtitle', 'alternative_titles')

        # get the work title (should have been checked it exists
        # before calling this method)
        work_title = dict_work.get('title')
        work_subtitle = dict_work.get('subtitle')

        for field in dict_work:
            if field not in field_names:
                logger.debug(
                        "Field '{}' for '{}' subtitled '{}' not in "
                        "fields taken into account.".format(
                            field,
                            work_title,
                            work_subtitle))

    def creatework(self, work_type_entry, dict_work):
        """Create or update a work in database."""

        # get the attributes of the work
        work_title = dict_work.get('title')
        work_subtitle = dict_work.get('subtitle', "")
        work_alternative_titles = dict_work.get('alternative_titles', [])

        # get or create works
        if self.update_only:

            try:
                work_entry = Work.objects.get(
                        title__iexact=work_title,
                        work_type=work_type_entry,
                        subtitle__iexact=work_subtitle)

            except Work.DoesNotExist:
                logger.debug("Work with attributes (title:{title}, "
                             "subtitle:{subtitle}, work_type:{work_type})"
                             " not found (update only).".format(
                                 title=work_title,
                                 subtitle=work_subtitle,
                                 work_type=work_type_entry.query_name))

                return

        else:
            work_entry, work_created = Work.objects.get_or_create(
                    title__iexact=work_title,
                    work_type=work_type_entry,
                    subtitle__iexact=work_subtitle,
                    defaults={
                        'title': work_title,
                        'work_type': work_type_entry,
                        'subtitle': work_subtitle}
                    )

            if work_created:
                logger.debug("Created work '{}'.".format(work_entry))

        # get work alternative titles or create them
        for alt_title in work_alternative_titles:
            self.create_alternative_title(
                    work_entry,
                    alt_title)

        # save work in the database
        work_entry.save()

    def create_alternative_title(self, work_entry, alt_title):
        """Create work alternative title in the database if necessary."""
        work_alt_title_entry, work_alt_title_created = WorkAlternativeTitle.objects.get_or_create( # noqa E501
                title__iexact=alt_title,
                work__title__iexact=work_entry.title,
                work__subtitle__iexact=work_entry.subtitle,
                defaults={
                    'title': alt_title,
                    'work': work_entry}
                )

        if work_alt_title_created:
            logger.debug("Created alternative"
                         " title '{}'.".format(work_alt_title_entry))

    def createworks(self):
        """Create or update works provided."""
        # parse the work file to get the data structure
        try:
            works = self.parser.parse_work(self.work_file)
        except BaseException as exc:
            raise CommandError("Error when reading the work"
                               " file: {}".format(exc)) from exc

        work_success = True
        # get works or create it
        for worktype_query_name, work_listing in works.items():

            logger.debug("Get work type '{}'".format(worktype_query_name))
            # get work type
            try:
                work_type_entry = WorkType.objects.get(
                        query_name__iexact=worktype_query_name
                        )

            except WorkType.DoesNotExist:
                work_success = False
                logger.error(
                    "Unable to find work type query name '{}'. Use "
                    "createworktypes command first to create "
                    "work types.".format(worktype_query_name))

            else:
                # check the value associated to the work_type is a list
                if not isinstance(work_listing, list):
                    work_success = False
                    logger.warning("Ignore creation of the works associated "
                                   "to the worktype '{}': "
                                   "value must be a list.".format(
                                       worktype_query_name))
                    continue

                # remove the works having an incorrect structure
                work_listing = self.remove_incorrect_works(work_listing)

                # get works and their attributes
                for dict_work in work_listing:

                    if self.debug:
                        self.debug_parser_work(dict_work)

                    self.creatework(work_type_entry, dict_work)

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

        parser.add_argument(
            "--update-only",
            help="""Only update the existing works with the creation of
            new alternative titles. Do not create new works.""",
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

        # debug
        debug = options.get('debug')
        if debug:
            logger.setLevel(logging.DEBUG)

        # update only
        update_only = options.get('update-only', False)

        work_creator = WorkCreator(
                work_file=work_file,
                parser=parser,
                debug=debug,
                update_only=update_only)

        # run the work creator
        work_creator.createworks()
