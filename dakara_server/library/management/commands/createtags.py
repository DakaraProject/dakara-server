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

    def handle_custom(self, config,  *args, **options):
        """ Setup the tags
        """
        for tag_name, color_id in config[self.SECTION_NAME].items():
            tag, _ = SongTag.objects.get_or_create(
                    name__iexact=tag_name,
                    defaults={'name': tag_name}
                    )

            tag.color_id = int(color_id)
            tag.save()

        self.stdout.write("Tags successfuly created")
