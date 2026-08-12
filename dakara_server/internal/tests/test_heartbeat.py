import pytest
from channels.testing import WebsocketCommunicator

from dakara_server.asgi import application


@pytest.mark.asyncio
class TestHeartbeat:
    async def test_connect(self):
        """Test to connect to heartbeats."""
        communicator = WebsocketCommunicator(application, "/ws/heartbeat/")

        # connect and check connection is established
        connected, _ = await communicator.connect()
        assert connected

        # close connection
        await communicator.disconnect()
