from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from library import models as library_models
from playlist import models as playlist_models

class Command(BaseCommand):
    help = 'Create default groups : Admin, User'


    def handle(self, *args, **options):
        admin, created = Group.objects.get_or_create(name="Admins")
        user, created = Group.objects.get_or_create(name="Users")

        permission_add_playlistentry = Permission.objects.get(codename="add_playlistentry")
        permission_delete_playlistentry = Permission.objects.get(codename="delete_playlistentry")
        permission_delete_own_playlistentry = Permission.objects.get(codename="delete_own_playlistentry")


        user.permissions.add(permission_add_playlistentry, permission_delete_own_playlistentry)
        admin.permissions.add(permission_add_playlistentry, permission_delete_playlistentry)

