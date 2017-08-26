from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

UserModel = get_user_model()
class BaseAPITestCase(APITestCase):

    def authenticate(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_user(self, username, playlist_level=None, library_level=None, users_level=None):
        user = UserModel.objects.create_user(username, "", "password")
        user.playlist_permission_level = playlist_level
        user.library_permission_level = library_level
        user.users_permission_level = users_level
        user.save()
        return user
