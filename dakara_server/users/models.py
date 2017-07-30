from django.contrib.auth.models import AbstractUser, UserManager


class DakaraUserManager(UserManager):
    def get_by_natural_key(self, username):
        return self.get(username__iexact=username)


class DakaraUser(AbstractUser):
    objects = DakaraUserManager()
