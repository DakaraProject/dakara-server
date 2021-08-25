from datetime import timedelta

import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.urls import reverse
from rest_framework import status

from dakara_server.asgi import application
from playlist import models


channel_layer = get_channel_layer()


@pytest.fixture
async def communicator(playlist_provider):
    """Gives a WebSockets communicator
    """
    # create a communicator
    communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

    # artificially give it a user
    communicator.scope["user"] = playlist_provider.player

    await communicator.connect()

    return communicator


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestDevice:
    async def test_authenticate_basic(self, playlist_provider):
        """Test to authenticate as the communicator fixture
        """
        # create a communicator
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

        # artificially give it a user
        communicator.scope["user"] = playlist_provider.player

        # check there is no communicator registered
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()
        assert karaoke.channel_name is None

        # connect and check connection is established
        connected, _ = await communicator.connect()
        assert connected

        # check communicator is registered
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()
        assert karaoke.channel_name is not None

        # close connection
        await communicator.disconnect()

    async def test_authenticate(self, playlist_provider):
        """Test to authenticate with a token

        This is the normal mechanism of real-life connection. In the tests, we
        assume the user is already in the scope.
        """
        # create a token
        headers = []
        playlist_provider.authenticate(playlist_provider.player, headers=headers)

        # create a communicator
        communicator = WebsocketCommunicator(
            application, "/ws/playlist/device/", headers=headers
        )

        # check there is no communicator registered
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()
        assert karaoke.channel_name is None

        # connect and check connection is established
        connected, _ = await communicator.connect()
        assert connected
        assert communicator.scope["user"] == playlist_provider.player

        # check communicator is registered
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()
        assert karaoke.channel_name is not None

        # close connection
        await communicator.disconnect()

    async def test_authenticate_player_twice_failed(self, playlist_provider):
        """Test to authenticate two players successively

        The second connection should be rejected.
        """
        # authenticate first player
        communicator_first = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator_first.scope["user"] = playlist_provider.player
        connected, _ = await communicator_first.connect()

        assert connected

        # authenticate second player
        communicator_second = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator_second.scope["user"] = playlist_provider.player
        connected, _ = await communicator_second.connect()

        assert not connected

        # close connections
        await communicator_first.disconnect()
        await communicator_second.disconnect()

    async def test_authenticate_user_failed(self, playlist_provider):
        """Test to authenticate as a normal user
        """
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator.scope["user"] = playlist_provider.user
        connected, _ = await communicator.connect()

        assert not connected

        # close connection
        await communicator.disconnect()

    async def test_authenticate_anonymous_user_failed(self, playlist_provider):
        """Test to authenticate as a anonymous user
        """
        # create a communicator
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

        # check there is no communicator registered
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()
        assert karaoke.channel_name is None

        # connect and check connection is not established
        connected, _ = await communicator.connect()
        assert not connected

        # check communicator is registered
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()
        assert karaoke.channel_name is None

        # close connection
        await communicator.disconnect()

    async def test_authenticate_playing_entry_playing(self, playlist_provider):
        """Test to authenticate when a playlist entry is supposed to be playing
        """
        # create a communicator
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator.scope["user"] = playlist_provider.player

        # set a playlist entry playing
        playlist_provider.player_play_next_song(timing=timedelta(seconds=10))
        playlist_entry = await database_sync_to_async(
            lambda: models.PlaylistEntry.objects.get_playing()
        )()
        assert playlist_entry is not None

        # connect and check connection is established
        connected, _ = await communicator.connect()
        assert connected

        # check there are no playing playlist entry
        playlist_entry = await database_sync_to_async(
            lambda: models.PlaylistEntry.objects.get_playing()
        )()
        assert playlist_entry is None

        # close connection
        await communicator.disconnect()

    async def test_receive_ready_send_playlist_entry(
        self, playlist_provider, player, communicator
    ):
        """Test that a new song is requested to play when the player is ready

        There are playlist entries awaiting to be played.
        """
        assert player.playlist_entry is None

        # send the event
        await communicator.send_json_to({"type": "ready"})

        # get the new song event
        event = await communicator.receive_json_from()
        assert event["type"] == "playlist_entry"
        assert event["data"]["id"] == playlist_provider.pe1.id

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_receive_ready_send_idle(
        self, playlist_provider, player, communicator
    ):
        """Test that idle screen is requested to play when the player is ready

        The playlist is empty.
        """
        # empty the playlist
        await database_sync_to_async(
            lambda: models.PlaylistEntry.objects.all().delete()
        )()

        assert player.playlist_entry is None

        # send the event
        await communicator.send_json_to({"type": "ready"})

        # get the new song event
        event = await communicator.receive_json_from()
        assert event["type"] == "idle"

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_playlist_entry(self, playlist_provider, player, communicator):
        """Test to send a new playlist entry to the device
        """
        # pre assert
        assert playlist_provider.pe1.date_played is None

        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # call the method
        await channel_layer.send(
            karaoke.channel_name,
            {"type": "send_playlist_entry", "playlist_entry": playlist_provider.pe1},
        )

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "playlist_entry"
        assert event["data"]["id"] == playlist_provider.pe1.id

        # assert there are no side effects
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_playlist_entry_failed_none(self, player, communicator):
        """Test a null playlist entry cannot be sent to the device
        """
        # pre assert
        assert player.playlist_entry is None

        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # call the method
        await channel_layer.send(
            karaoke.channel_name,
            {"type": "send_playlist_entry", "playlist_entry": None},
        )

        # wait the outcoming event
        with pytest.raises(ValueError):
            await communicator.wait()

        # assert there are no side effects
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # no need to close connection

    async def test_send_idle(self, playlist_provider, player, communicator):
        """Test to send a new playlist entry to the device
        """
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # call the method
        await channel_layer.send(karaoke.channel_name, {"type": "send_idle"})

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "idle"

        # assert there are no side effects
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_pause(self, playlist_provider, player, communicator):
        """Test to send to the player a pause command
        """
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # call the method
        await channel_layer.send(
            karaoke.channel_name, {"type": "send_command", "command": "pause"}
        )

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "command"
        assert event["data"]["command"] == "pause"

        # assert there are no side effects
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_play(self, playlist_provider, player, communicator):
        """Test to send to the player a play command
        """
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # call the method
        await channel_layer.send(
            karaoke.channel_name, {"type": "send_command", "command": "play"}
        )

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "command"
        assert event["data"]["command"] == "play"

        # assert there are no side effects
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_skip(self, playlist_provider, player, communicator):
        """Test to send to the player a skip command
        """
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # call the method
        await channel_layer.send(
            karaoke.channel_name, {"type": "send_command", "command": "skip"}
        )

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "command"
        assert event["data"]["command"] == "skip"

        # assert there are no side effects
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_failed(self, player, communicator):
        """Test an invalid command cannot be sent to the player
        """
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # call the method
        await channel_layer.send(
            karaoke.channel_name, {"type": "send_command", "command": "unknown"}
        )

        # wait the outcoming event
        with pytest.raises(ValueError):
            await communicator.wait()

        # assert there are no side effects
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # no need to close connection

    async def test_send_handle_next(
        self, playlist_provider, player, communicator, client_drf, mocker
    ):
        """Test to handle next playlist entries untill the end of the playlist
        """
        # configure HTTP client
        url = reverse("playlist-player-status")
        playlist_provider.authenticate(playlist_provider.player, client=client_drf)

        # mock the broadcaster
        # we cannot call it within an asynchronous test
        mocker.patch("playlist.views.send_to_channel")
        # mocked_send_to_channel = mocker.patch("playlist.views.send_to_channel")

        # assert kara is ongoing and player play next song
        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()
        assert karaoke.ongoing
        assert karaoke.player_play_next_song

        # assert player is currently idle
        assert player.playlist_entry is None

        # play the first playlist entry
        await channel_layer.send(karaoke.channel_name, {"type": "handle_next"})

        # wait for the event of the first playlist entry to play
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "playlist_entry"
        assert event["data"]["id"] == playlist_provider.pe1.id

        # notify the first playlist entry is being played
        response = client_drf.put(
            url,
            data={
                "event": "started_transition",
                "playlist_entry_id": playlist_provider.pe1.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        response = client_drf.put(
            url,
            data={
                "event": "started_song",
                "playlist_entry_id": playlist_provider.pe1.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player.playlist_entry == playlist_provider.pe1

        # # assert the front has been notified
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

        # notify the first playlist entry has finished
        response = client_drf.put(
            url,
            data={"event": "finished", "playlist_entry_id": playlist_provider.pe1.id},
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player.playlist_entry is None

        # play the second playlist entry
        await channel_layer.send(karaoke.channel_name, {"type": "handle_next"})

        # wait for the event of the second playlist entry to play
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "playlist_entry"
        assert event["data"]["id"] == playlist_provider.pe2.id

        # notify the second playlist entry is being played
        response = client_drf.put(
            url,
            data={
                "event": "started_transition",
                "playlist_entry_id": playlist_provider.pe2.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        response = client_drf.put(
            url,
            data={
                "event": "started_song",
                "playlist_entry_id": playlist_provider.pe2.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player.playlist_entry == playlist_provider.pe2

        # notify the second playlist entry has finished
        response = client_drf.put(
            url,
            data={"event": "finished", "playlist_entry_id": playlist_provider.pe2.id},
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player.playlist_entry is None

        # # assert the front has been notified
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

        # now the playlist should be empty
        await channel_layer.send(karaoke.channel_name, {"type": "handle_next"})

        # wait for the event of idle
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "idle"

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_handle_next_karaoke_not_ongoing(
        self, playlist_provider, player, communicator
    ):
        """Test to handle next playlist entries when the karaoke is not ongoing
        """
        # set the karaoke not ongoing
        await database_sync_to_async(
            lambda: playlist_provider.set_karaoke(ongoing=False)
        )()

        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # empty the playlist
        await database_sync_to_async(
            lambda: models.PlaylistEntry.objects.all().delete()
        )()

        # assert player is currently idle
        assert player.playlist_entry is None

        # the playlist should be empty
        await channel_layer.send(karaoke.channel_name, {"type": "handle_next"})

        # wait for the event of idle
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "idle"

        # assert the player has not changed
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player == player_new

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_handle_next_karaoke_not_play_next_song(
        self, playlist_provider, player, communicator
    ):
        """Test to handle next playlist entries when the player does not play next song
        """
        # set player does not play next song
        await database_sync_to_async(
            lambda: playlist_provider.set_karaoke(player_play_next_song=False)
        )()

        karaoke = await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

        # assert player is currently idle
        assert player.playlist_entry is None

        # there should not be anything to play for now
        await channel_layer.send(karaoke.channel_name, {"type": "handle_next"})

        # wait for the event of idle
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "idle"

        # assert the player has not changed
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player == player_new

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_connect_reset_playing_playlist_entry(
        self, playlist_provider, player
    ):
        """Test to reset playing playlist entry
        """
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator.scope["user"] = playlist_provider.player
        connected, _ = await communicator.connect()

        # set player playing
        await database_sync_to_async(
            lambda: playlist_provider.player_play_next_song()
        )()
        assert player.playlist_entry is not None

        # disconnect and reconnect the player
        await communicator.disconnect()
        communicator_new = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator_new.scope["user"] = playlist_provider.player
        connected, _ = await communicator_new.connect()

        # check that the player is idle
        player_new, _ = await database_sync_to_async(
            lambda: models.Player.objects.get_or_create(
                id=models.Karaoke.objects.get_object().id
            )
        )()
        assert player_new.playlist_entry is None

        await communicator_new.disconnect()

    async def test_disconnect_player_while_playing(
        self, playlist_provider, player, communicator
    ):
        """Test that current playlist entry is reseted when player is disconnected
        """
        # start playing a song
        await database_sync_to_async(
            lambda: playlist_provider.player_play_next_song(timing=timedelta(seconds=1))
        )()
        assert player.playlist_entry == playlist_provider.pe1

        # stop the player connection
        await communicator.disconnect()

        # assert the play is stopped
        assert player.playlist_entry is None
        assert player.timing == timedelta()

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done
