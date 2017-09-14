#!/usr/bin/env python3
##
# Dakaraneko Project
#
# Script for setting up tags
#

from ._private import BaseCommandWithConfig, CommandError
from library.models import SongTag


class Command(BaseCommandWithConfig):
    """ Command to create tags
    """
    help = "Setup tags."
    SECTION_NAME = "tags"

    def handle_custom(self, tags,  *args, **options):
        """ Setup the tags

            In the config file providing tags, the branch contains a list
                of dictionnaries with the keys `name` and `color_id`. The `name`
                key is mandatory.
        """
        for tag in tags:
            # check there is a query name
            if 'name' not in tag:
                raise ValueError("A tag must have a name")

            # get the tag from database or create it
            tag_entry, _ = SongTag.objects.get_or_create(
                    name__iexact=tag['name'],
                    defaults={'name': tag['name']}
                    )

            # process extra field
            if tag['color_id']:
                tag_entry.color_id = int(tag['color_id'])
                tag_entry.save()

        self.stdout.write("Tags successfuly created")
