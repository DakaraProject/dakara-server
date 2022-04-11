import pytest_asyncio
from channels.db import database_sync_to_async
from rest_framework.test import APIClient


@database_sync_to_async
def get_playlist_provider():
    from playlist.tests.base_test import PlaylistProvider

    provider = PlaylistProvider()
    provider.create_test_data()
    return provider


@pytest_asyncio.fixture
async def playlist_provider():
    return await get_playlist_provider()


@pytest_asyncio.fixture
def client_drf():
    return APIClient()
