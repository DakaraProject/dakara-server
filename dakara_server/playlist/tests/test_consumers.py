import pytest
from channels.layers import get_channel_layer

from playlist import consumers


channel_layer = get_channel_layer()


class TestDispatchJsonWebsocketConsumer:
    """Test the DispatchJsonWebsocketConsumer class
    """

    class DummyConsumer(consumers.DispatchJsonWebsocketConsumer):
        def receive_dummy(self, data):
            pass

    def test_receive_json(self, mocker):
        """Test to call the appropriate method on receive
        """
        mocked_receive_dummy = mocker.patch.object(self.DummyConsumer, "receive_dummy")

        consumer = self.DummyConsumer({})
        consumer.receive_json({"type": "dummy", "data": "data"})

        mocked_receive_dummy.assert_called_with("data")

    def test_receive_json_no_method(self, caplog):
        """Test to call a non existent method on receive
        """
        consumer = self.DummyConsumer({})
        consumer.receive_json({"type": "non_existent", "data": "data"})

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert (
            caplog.records[0].getMessage()
            == "Event of unknown type received 'non_existent'"
        )


class TestSendToChannel:
    """Test the send_to_channel function
    """

    def test_send_to_device(self, mocker):
        """Test to send an event to the device consumer
        """
        mocked_get_channel_name = mocker.patch.object(
            consumers.PlaylistDeviceConsumer, "get_channel_name"
        )
        mocked_get_channel_name.return_value = "channel name"
        mocked_async_to_sync = mocker.patch("playlist.consumers.async_to_sync")

        consumers.send_to_channel("playlist.device", "type", {"key": "value"})

        mocked_async_to_sync.assert_called_with(channel_layer.send)
        mocked_async_to_sync.return_value.assert_called_with(
            "channel name", {"type": "type", "key": "value"}
        )

    def test_send_to_unknown(self, mocker):
        """Test to send an event to unknown consumer
        """
        mocked_async_to_sync = mocker.patch("playlist.consumers.async_to_sync")

        with pytest.raises(
            consumers.UnknownConsumerError,
            match="Unknown consumer name requested 'unknown'",
        ):
            consumers.send_to_channel("unknown", "type", {"key": "value"})

        mocked_async_to_sync.assert_not_called()

    def test_send_to_channel_no_name(self, mocker):
        """Test to send an event to a consumer with no name
        """
        mocked_async_to_sync = mocker.patch("playlist.consumers.async_to_sync")
        mocked_get_channel_name = mocker.patch.object(
            consumers.PlaylistDeviceConsumer, "get_channel_name"
        )
        mocked_get_channel_name.return_value = None

        consumers.send_to_channel("playlist.device", "type", {"key": "value"})

        mocked_async_to_sync.assert_not_called()
