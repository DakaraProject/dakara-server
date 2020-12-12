#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "dakara_server.settings.development"
    )
    os.environ.setdefault("HOST_URL", "http://localhost:3000")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
