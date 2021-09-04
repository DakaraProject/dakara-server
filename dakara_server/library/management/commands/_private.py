import os
import sys
from codecs import open

import yaml
from django.core.management.base import BaseCommand, CommandError

file_encoding = sys.getfilesystemencoding()


class BaseCommandWithConfig(BaseCommand):
    """Base command class for handling config file
    """

    SECTION_NAME = ""

    def add_arguments(self, parser):
        """Extend arguments for the command
        """
        parser.add_argument("config-file", help="Config file.")

        parser.add_argument(
            "--quiet", help="Do not display anything on run.", action="store_true"
        )

        self.add_arguments_custom(parser)

    def add_arguments_custom(self, parser):
        """Stub for extra arguments for the command
        """

    def handle(self, *args, **options):
        """Setup the tags
        """
        # quiet mode
        if options["quiet"]:
            self.stdout = open(os.devnull, "w")
            self.stderr = open(os.devnull, "w")

        # check config file
        config_file = options["config-file"]
        config_file_encoded = config_file.encode(file_encoding)
        if not os.path.isfile(config_file_encoded):
            raise CommandError("Config file '{}' not found".format(config_file))

        # open config file
        with open(config_file_encoded, "r", "utf8") as file:
            config = yaml.load(file.read())

        # check tag section exists
        if self.SECTION_NAME not in config:
            raise CommandError(
                "Invalid YAML config file, no branch '{}'".format(self.SECTION_NAME)
            )

        self.handle_custom(config[self.SECTION_NAME], *args, **options)

    def handle_custom(self, config, *args, **options):
        """Stub for custom handle actions
        """
