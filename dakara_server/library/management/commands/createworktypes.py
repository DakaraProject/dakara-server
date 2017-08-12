#!/usr/bin/env python3
##
# Dakaraneko Project
#
# Script for setting up worktypes
#

from ._private import BaseCommandWithConfig, CommandError
from library.models import WorkType


class Command(BaseCommandWithConfig):
    """ Command to create work types
    """
    help = "Setup work types."
    SECTION_NAME = "worktypes"

    def _get_subkeys(self):
        """ Extract the keys from the model and ignore the ones we don't need
        """
        return (f.name for f in WorkType._meta.fields
                if f.name not in ('id', 'query_name'))

    def add_arguments_custom(self, parser):
        """ Extra arguments for the command
        """
        parser.epilog = (
                "Authorized subkeys for work types are '" +
                "', '".join(self._get_subkeys()) +
                "'."
                )

    def handle_custom(self, config, *args, **options):
        """ Setup the tags
        """
        for key, value in config.items():
            # process for all subkeys
            for subkey in self._get_subkeys():
                dot_subkey = '.' + subkey
                if key.endswith(dot_subkey):
                    # get the query name which is the key minus the subkey
                    query_name = key[:-len(dot_subkey)]

                    work_type, _ = WorkType.objects.get_or_create(
                            query_name__iexact=query_name,
                            defaults={'query_name': query_name}
                            )

                    # alter the work type attribute
                    setattr(work_type, subkey, value)
                    work_type.save()

        self.stdout.write("Work links successfuly created")
