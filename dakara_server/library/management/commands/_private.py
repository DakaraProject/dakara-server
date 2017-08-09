##
# Dakaraneko Project
#
# Base command class for handling config file
#

import os
from django.core.management.base import BaseCommand, CommandError
from configparser import ConfigParser

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
        if not os.path.isfile(config_file):
            raise CommandError(
                    "Config file '{}' not found".format(config_file)
                    )

        # open config file
        config = ConfigParser()
        config.read(config_file)

        # check tag section exists
        if not config.has_section(self.SECTION_NAME):
            raise CommandError(
                    "Invalid config file, no section '{}'".format(self.SECTION_NAME)
                    )

        self.handle_custom(config, *args, **options)

    def handle_custom(self, config, *args, **options):
        """ Stub for custom handle actions
        """
