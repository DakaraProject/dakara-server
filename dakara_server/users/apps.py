from internal.apps import DakaraConfig


class UsersConfig(DakaraConfig):
    """Users app
    """

    name = "users"

    def ready(self):
        import users.signals  # noqa F401
