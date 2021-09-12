from internal.apps import DakaraConfig


class UsersConfig(DakaraConfig):
    """Users app."""

    name = "users"

    def ready_reload(self):
        """Method called when app and reloader start."""
        import users.signals  # noqa F401
