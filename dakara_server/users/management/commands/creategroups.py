from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from library import models as library_models
from playlist import models as playlist_models

class Command(BaseCommand):
    help = 'Create default groups : Admin, User'

    def handle(self, *args, **options):
        player, created = Group.objects.get_or_create(name="Player")
        users_manager, created = Group.objects.get_or_create(name="Users Manager")
        playlist_manager, created = Group.objects.get_or_create(name="Playlist Manager")
        playlist_user, created = Group.objects.get_or_create(name="Playlist User")
        library_manager, created = Group.objects.get_or_create(name="Library Manager")
