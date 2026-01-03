import time

from django.core.management.base import BaseCommand
from django.db.utils import InterfaceError, OperationalError


class Command(BaseCommand):
    help = "Wait for the database to be ready"

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for database...")
        db_up = False
        try:
            while db_up is False:
                try:
                    self.check(databases=["default"])
                    db_up = True

                except (OperationalError, InterfaceError):
                    self.stdout.write("Database unavailable, waiting for 5 second...")
                    time.sleep(5)

        except KeyboardInterrupt:
            self.stdout.write("Aborted by user")
            return

        self.stdout.write(self.style.SUCCESS("Database available!"))
