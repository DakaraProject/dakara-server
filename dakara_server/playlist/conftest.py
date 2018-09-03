import pytest
from channels.db import database_sync_to_async
from rest_framework.test import APIClient

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
def client_drf():
    return APIClient()


@pytest.fixture
def player():
    player = Player()
    player.save()
    return player
