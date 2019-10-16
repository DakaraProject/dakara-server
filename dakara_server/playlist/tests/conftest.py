import pytest
from channels.db import database_sync_to_async
from rest_framework.test import APIClient

from playlist.models import Player
from playlist.tests.base_test import PlaylistProvider


@database_sync_to_async
def get_playlist_provider():
    provider = PlaylistProvider()
    provider.create_test_data()
    return provider


@pytest.fixture
async def playlist_provider():
    return await get_playlist_provider()


@pytest.fixture
def client_drf():
    return APIClient()


@pytest.fixture
def player():
    player = Player()
    player.save()
    return player
