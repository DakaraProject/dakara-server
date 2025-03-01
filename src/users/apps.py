from internal.apps import DakaraConfig
from users import signals  # noqa F401


class UsersConfig(DakaraConfig):
    """Users app."""

    name = "users"
