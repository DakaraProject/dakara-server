import pytest
from channels.db import database_sync_to_async

from playlist.base_test import Provider
from playlist.models import Player


@database_sync_to_async
def get_provider():
    provider = Provider()
    provider.create_test_data()
    return provider


@pytest.fixture
async def provider():
    return await get_provider()


@pytest.fixture
def player():
    player = Player.get_or_create()
    player.reset()
    player.save()
    return player
