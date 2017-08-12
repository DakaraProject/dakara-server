##
# Dakaraneko Project
#
# Base command class for handling config file
#

import os
import sys
from django.core.management.base import BaseCommand, CommandError
from configparser import ConfigParser
from codecs import open


file_encoding = sys.getfilesystemencoding()


class BaseCommandWithConfig(BaseCommand):
    """ Base command class for handling config file
    """
    SECTION_NAME = ""

    def add_arguments(self, parser):
        """ Extend arguments for the command
        """
        parser.add_argument(
                "config-file",
                help="Config file."
                )

    def handle(self, *args, **options):
        """ Setup the tags
        """
        # check config file
        config_file = options['config-file']
        config_file_encoded = config_file.encode(file_encoding)
        if not os.path.isfile(config_file_encoded):
            raise CommandError(
                    "Config file '{}' not found".format(config_file)
                    )

        # open config file
        config = ConfigParser()
        with open(config_file_encoded, "r", "utf8") as file:
            config.readfp(file)

        # check tag section exists
        if not config.has_section(self.SECTION_NAME):
            raise CommandError(
                    "Invalid config file, no section '{}'".format(self.SECTION_NAME)
                    )

        self.handle_custom(config, *args, **options)

    def handle_custom(self, config, *args, **options):
        """ Stub for custom handle actions
        """
