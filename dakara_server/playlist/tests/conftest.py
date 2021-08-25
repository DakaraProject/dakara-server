import pytest
from channels.db import database_sync_to_async
from rest_framework.test import APIClient


@database_sync_to_async
def get_playlist_provider():
    from playlist.tests.base_test import PlaylistProvider

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
    from playlist.models import Karaoke, Player

    karaoke = Karaoke.objects.get_object()
    player, _ = Player.objects.get_or_create(id=karaoke.id)
    return player
