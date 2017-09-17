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

    def handle_custom(self, work_types, *args, **options):
        """ Setup the tags

            In the config file providing work types, the branch contains a list
                of dictionnaries with different keys. Among them, the
                `query_name` key is mandatory.
        """
        for work_type in work_types:
            # check there is a query name
            if 'query_name' not in work_type:
                raise ValueError("A work type must have a query name")

            # get the work entry from database or creat it
            work_type_entry, _ = WorkType.objects.get_or_create(
                    query_name__iexact=work_type['query_name'],
                    defaults={'query_name': work_type['query_name']}
                    )

            # process for all extra fields
            for subkey in self._get_subkeys():
                if subkey not in work_type:
                    continue

                # alter the work type attribute
                setattr(work_type_entry, subkey, work_type[subkey])
                work_type_entry.save()

        if not options.get('quiet'):
            self.stdout.write("Work types successfuly created")
