from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

UserModel = get_user_model()

USERNAME_DEFAULT = "player"


class Command(BaseCommand):
    """Create the player special user
    """

    help = "Create player account."

    def add_arguments(self, parser):
        """Add arguments for the command

        Args:
            parser (argparse.ArgumentParser): Parser.
        """

        parser.add_argument(
            "--username",
            help="Specifies the loging for the player. Default to '{}'.".format(
                USERNAME_DEFAULT
            ),
        )
        parser.add_argument("--password", help="Specifies the password for the player.")
        parser.add_argument(
            "--noinput",
            help="Tells Django to NOT prompt the user for input of any kind. "
            "Use command line arguments only.",
            action="store_true",
        )

    @staticmethod
    def get_username():
        """Get username from user

        Returns:
            str: Username.
        """
        username = input("Username (default: '{}'): ".format(USERNAME_DEFAULT))
        return username or USERNAME_DEFAULT

    def get_password(self):
        """Get password from user

        Returns:
            str: Password.
        """
        while True:
            password = getpass()
            password_confirm = getpass("Password (again): ")

            if not password == password_confirm:
                self.stderr.write("Error: Your passwords didn't match.")
                continue

            return password

    def create_player(self, username, password):
        """Create player from provided credentials

        Args:
            username (str): Username for the player.
            password (str): Password for the player.
        """
        # check password
        if not password:
            self.stderr.write("Error: Blank passwords aren't allowed.")
            return

        try:
            UserModel.objects.create_user(
                username,
                password=password,
                email="{}@player".format(username),
                validated_by_email=True,
                validated_by_manager=True,
                playlist_permission_level=UserModel.PLAYER,
            )

        except (IntegrityError, ValueError) as e:
            self.stderr.write("Error: {}".format(e))
            return

        self.stdout.write("Player created successfully.")

    def handle(self, *args, **options):
        """Handle the command
        """
        # in non interactive mode
        if options["noinput"]:
            self.create_player(
                (options["username"] or USERNAME_DEFAULT), options["password"]
            )
            return

        # interactive mode
        # username
        if options["username"]:
            username = options["username"]

        else:
            username = self.get_username()

        # password
        if options["password"]:
            password = options["password"]

        else:
            password = self.get_password()

        self.create_player(username, password)
