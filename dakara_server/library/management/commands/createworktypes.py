#!/usr/bin/env python3
##
# Dakaraneko Project
#
# Script for setting up worktypes
#

from ._private import BaseCommandWithConfig, CommandError
from library.models import WorkType


SUBKEYS = ("name", "icon_name")


class Command(BaseCommandWithConfig):
    """ Command to create work types
    """
    help = "Setup work types."
    SECTION_NAME = "worktypes"

    def handle_custom(self, config, *args, **options):
        """ Setup the tags
        """
        for key, value in config[self.SECTION_NAME].items():
            # process for all subkeys
            for subkey in SUBKEYS:
                dot_subkey = '.' + subkey
                if key.endswith(dot_subkey):
                    query_name = key[:-len(dot_subkey)]
                    work_type, _ = WorkType.objects.get_or_create(
                            query_name__iexact=query_name,
                            defaults={'query_name': query_name}
                            )

                    setattr(work_type, subkey, value)
                    work_type.save()

        self.stdout.write("Work links successfuly created")
