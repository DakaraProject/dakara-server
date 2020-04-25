import os
import sys
import logging
import importlib

from django.core.management.base import BaseCommand, CommandError

from library.models import WorkType, WorkAlternativeTitle, Work

from .components import default_work_parser

# get logger
logger = logging.getLogger(__name__)


class WorkAlternativeTitleCreator:
    """Work alternative title creator"""

    def remove_incorrect_alt_titles(self, work_alternative_titles):
        """Remove the alternative titles having an incorrect structure

        Args:
            work_alternative_titles (list): The list of alt titles to filter

        Returns:
            list: The new list with the incorrect alternative titles removed.

        """
        alt_title_to_remove = []

        for index, struct_alt_title in enumerate(work_alternative_titles):
            # check if it is a string
            if not isinstance(struct_alt_title, str):
                alt_title_to_remove.append(struct_alt_title)
                logger.debug(
                    "Incorrect alternative title at index {} of "
                    "current work: value must be a string.".format(index)
                )

        return [
            alt_title
            for alt_title in work_alternative_titles
            if alt_title not in alt_title_to_remove
        ]

    def create_alternative_title(self, work_type_entry, work_entry, alt_title):
        """Create work alternative title in the database if necessary

        Args:
            work_type_entry (obj): The work type entry for the alt title
            work_entry (obj): The work entry for the alt title
            alt_title (str): The work alternative title to create if necessary

        """
        alt_title_entry, created = WorkAlternativeTitle.objects.get_or_create(
            title=alt_title,
            work__title=work_entry.title,
            work__work_type=work_type_entry,
            work__subtitle=work_entry.subtitle,
            defaults={"title": alt_title, "work": work_entry},
        )

        if created:
            logger.debug("Created alternative" " title '{}'.".format(alt_title_entry))

    def create_alternative_titles(
        self, work_type_entry, work_entry, work_alternative_titles
    ):
        """Create work alternative titles of a work

        Args:
            work_type_entry (obj): The work type entry for these alt titles
            work_entry (obj): The work entry for these alt titles
            work_alternative_titles (list): The list of alt titles to create

        """
        # remove the incorrect alternative titles
        work_alternative_titles = self.remove_incorrect_alt_titles(
            work_alternative_titles
        )

        for alt_title in work_alternative_titles:
            # create work alternative title
            self.create_alternative_title(work_type_entry, work_entry, alt_title)


class WorkCreator:
    """Work creator and updater

    Create and update works in the database provided a work file and a parser.

    Attributes:
        work_file (str): Absolute path of the file storing the works data
        parser (module): Custom python module used to extract data from file
        debug (bool): Enable debug mode if true
        update_only (bool): Only update existing works, do not create new ones

    About parser:
        This module should define a method called `parse_work` which takes
        a file path as argument and return a dictionnary with the following:
            works (dict): keys are a query name worktype, values are
            a list such that each element of this list is a dictionnary with
            the following keys:
                title (str): title of the work (required)
                subtitle (str): subtitle of the work (required)
                alternative_titles (list): list of alternative titles of
                a work

            Example of correct works dictionary:
                {'WorkType 1':
                    [
                        {'title': 'Work 1', 'subtitle': 'Subtitle 1',
                         'alternative_titles': ['AltTitle 1', 'AltTitle 2']},
                        {'title': 'Work 2', 'subtitle': 'Subtitle 2'}
                    ],
                 'WorkType 2': []}

    """

    def __init__(self, work_file="", parser=None, debug=False, update_only=False):
        self.work_file = work_file
        self.parser = parser
        self.debug = debug
        self.update_only = update_only
        self.work_alt_title_creator = WorkAlternativeTitleCreator()

    def remove_incorrect_works(self, work_listing):
        """Remove works having an incorrect structure in a list of works

        Args:
            work_listing (list): The list of works to filter

        Returns:
            list: The new list with the incorrect works removed

        """
        work_to_remove = []

        logger.debug("Removing the incorrect work from the current work type.")
        for index, dict_work in enumerate(work_listing):
            # check if it is a dictionary
            if not isinstance(dict_work, dict):
                work_to_remove.append(dict_work)
                logger.debug(
                    "Incorrect work at index {}: "
                    "value must be a dictionary.".format(index)
                )
                continue

            # check if it has a title field
            work_title = dict_work.get("title")
            if not work_title:
                work_to_remove.append(dict_work)
                logger.debug("Incorrect work at index {}: " "no title field found")
                continue

            logger.debug(
                "Work '{}' at index '{}' is correctly structured.".format(
                    work_title, index
                )
            )

        return [work for work in work_listing if work not in work_to_remove]

    def creatework(self, work_type_entry, dict_work):
        """Create or update a work in database

        Args:
            work_type_entry (obj): The work type entry object of the work
            dict_work (dict): The work as a dictionary (see parser doc)

        """
        # get the attributes of the work
        work_title = dict_work.get("title")
        work_subtitle = dict_work.get("subtitle", "")
        work_alternative_titles = dict_work.get("alternative_titles", [])

        logger.debug(
            "Get Work (title: {title}, "
            "subtitle: {subtitle}, work_type: {work_type})".format(
                title=work_title,
                subtitle=work_subtitle,
                work_type=work_type_entry.query_name,
            )
        )

        # get or create works
        if self.update_only:
            try:
                work_entry = Work.objects.get(
                    title=work_title, work_type=work_type_entry, subtitle=work_subtitle
                )

            except Work.DoesNotExist:
                logger.debug(
                    "Work (title: {title}, "
                    "subtitle: {subtitle}, work_type: {work_type})"
                    " not found (update only).".format(
                        title=work_title,
                        subtitle=work_subtitle,
                        work_type=work_type_entry.query_name,
                    )
                )

                return

        else:
            work_entry, work_created = Work.objects.get_or_create(
                title=work_title,
                work_type=work_type_entry,
                subtitle=work_subtitle,
                defaults={
                    "title": work_title,
                    "work_type": work_type_entry,
                    "subtitle": work_subtitle,
                },
            )

            if work_created:
                logger.debug("Created work '{}'.".format(work_entry))

        # get work alternative titles or create them
        self.work_alt_title_creator.create_alternative_titles(
            work_type_entry, work_entry, work_alternative_titles
        )

        # save work in the database
        work_entry.save()

    def createworks(self):
        """Create or update works provided

        Note:
            Raise a CommandError exception if the work file cannot be read

        """
        # parse the work file to get the data structure
        try:
            works = self.parser.parse_work(self.work_file)
        except BaseException as exc:
            raise CommandError(
                "Error when reading the work" " file: {}".format(exc)
            ) from exc

        work_success = True
        # get works or create it
        for worktype_query_name, work_listing in works.items():
            logger.debug("Get WorkType query name '{}'".format(worktype_query_name))
            # get work type
            try:
                work_type_entry = WorkType.objects.get(query_name=worktype_query_name)

            except WorkType.DoesNotExist:
                work_success = False
                logger.error(
                    "Unable to find work type query name '{}'. Use "
                    "createworktypes command first to create "
                    "work types.".format(worktype_query_name)
                )
                continue

            # check the value associated to the work_type is a list
            if not isinstance(work_listing, list):
                work_success = False
                logger.warning(
                    "Ignore creation of the works associated "
                    "to the worktype '{}': "
                    "value must be a list.".format(worktype_query_name)
                )
                continue

            # remove the works having an incorrect structure
            work_listing = self.remove_incorrect_works(work_listing)

            # get works and their attributes
            for dict_work in work_listing:
                self.creatework(work_type_entry, dict_work)

        if work_success:
            logger.info("Works successfully created.")


class Command(BaseCommand):
    """Command available for `manage.py` for creating works or add info"""

    help = "Create works or add extra information to works."

    def add_arguments(self, parser):
        """Extend arguments for the command"""
        parser.add_argument(
            "work-file", help="Path of the file storing the works data."
        )

        parser.add_argument(
            "--parser",
            help="""Name of a custom python module used to extract data from file name;
            see internal doc for what is expected for this module.""",
            default=None,
        )

        parser.add_argument(
            "-d", "--debug", help="Display debug messages.", action="store_true"
        )

        parser.add_argument(
            "--update-only",
            help="""Only update the existing works with the creation of
            new alternative titles. Do not create new works.""",
            action="store_true",
        )

    def handle(self, *args, **options):
        """Process the feeding"""
        # work file data
        work_file = os.path.normpath(options["work-file"])

        # parser
        if options.get("parser"):
            parser_directory = os.path.join(
                os.getcwd(), os.path.dirname(options["parser"])
            )

            parser_name, _ = os.path.splitext(os.path.basename(options["parser"]))
            sys.path.append(parser_directory)
            parser = importlib.import_module(parser_name)
        else:
            parser = default_work_parser

        # debug
        debug = options.get("debug")
        if debug:
            logger.setLevel(logging.DEBUG)

        # update only
        update_only = options.get("update_only", False)

        work_creator = WorkCreator(
            work_file=work_file, parser=parser, debug=debug, update_only=update_only
        )

        # run the work creator
        work_creator.createworks()
