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
async def communicator(get_player_token):
    """Gives a WebSockets communicator."""
    # create a communicator
    communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

    # artificially set player token
    token = await get_player_token()
    communicator.scope["headers"].append(
        (b"authorization", ("Token " + token).encode())
    )

    await communicator.connect()

    return communicator


@pytest.fixture
async def get_karaoke():
    """Allows to retrieve a karaoke"""

    async def func():
        return await database_sync_to_async(
            lambda: models.Karaoke.objects.get_object()
        )()

    return func


@pytest.fixture
async def get_player(get_karaoke):
    """Allows to retrieve a player"""

    async def func():
        karaoke = await get_karaoke()
        player, _ = await database_sync_to_async(
            lambda: models.Player.cache.get_or_create(karaoke=karaoke)
        )()

        return player

    return func


@pytest.fixture
async def get_player_token(get_karaoke):
    """Gives a player token"""

    async def func():
        karaoke = await get_karaoke()
        token, _ = await database_sync_to_async(
            lambda: models.PlayerToken.objects.get_or_create(karaoke=karaoke)
        )()

        return token.key

    return func


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestDevice:
    async def test_authenticate(self, get_karaoke, get_player_token):
        """Test to authenticate as the communicator fixture."""
        # create a communicator
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

        # give it a valid token
        token = await get_player_token()
        communicator.scope["headers"].append(
            (b"authorization", ("Token " + token).encode())
        )

        # check there is no communicator registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is None

        # connect and check connection is established
        connected, _ = await communicator.connect()
        assert connected

        # check communicator is registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is not None

        # close connection
        await communicator.disconnect()

    async def test_authenticate_no_token_generated_failed(self, get_karaoke):
        """Test to authenticate when no player token exists."""
        # create a communicator
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

        # give it an invalid token
        communicator.scope["headers"].append((b"authorization", b"Token 1234abcd"))

        # check there is no communicator registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is None

        # connect and check connection is established
        connected, _ = await communicator.connect()
        assert not connected

        # check there are communicator registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is None

        # close connection
        await communicator.disconnect()

    async def test_authenticate_invalid_token_failed(
        self, get_karaoke, get_player_token
    ):
        """Test to authenticate with an invalid token."""
        # create a communicator
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

        # give it an invalid token
        await get_player_token()
        communicator.scope["headers"].append((b"authorization", b"Token 1234abcd"))

        # check there is no communicator registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is None

        # connect and check connection is established
        connected, _ = await communicator.connect()
        assert not connected

        # check there are communicator registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is None

        # close connection
        await communicator.disconnect()

    async def test_authenticate_twice_failed(self, get_player_token):
        """Test to authenticate two players successively.

        The second connection should be rejected.
        """
        token = await get_player_token()

        # authenticate first player
        communicator_first = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator_first.scope["headers"].append(
            (b"authorization", ("Token " + token).encode())
        )
        connected, _ = await communicator_first.connect()

        assert connected

        # authenticate second player
        communicator_second = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator_second.scope["headers"].append(
            (b"authorization", ("Token " + token).encode())
        )
        connected, _ = await communicator_second.connect()

        assert not connected

        # close connections
        await communicator_first.disconnect()
        await communicator_second.disconnect()

    async def test_authenticate_normal_user_failed(self, playlist_provider):
        """Test to authenticate as a normal user."""
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator.scope["user"] = playlist_provider.user
        connected, _ = await communicator.connect()

        assert not connected

        # close connection
        await communicator.disconnect()

    async def test_authenticate_anonymous_user_failed(self, get_karaoke):
        """Test to authenticate as a anonymous user."""
        # create a communicator
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")

        # check there is no communicator registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is None

        # connect and check connection is not established
        connected, _ = await communicator.connect()
        assert not connected

        # check communicator is registered
        karaoke = await get_karaoke()
        assert karaoke.channel_name is None

        # close connection
        await communicator.disconnect()

    async def test_authenticate_playlist_entry_playing(
        self, playlist_provider, get_player, get_player_token
    ):
        """Test to authenticate when a playlist entry is supposed to be playing."""
        # create a communicator
        token = await get_player_token()
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator.scope["headers"].append(
            (b"authorization", ("Token " + token).encode())
        )

        # set a playlist entry playing
        playlist_provider.player_play_next_song(timing=timedelta(seconds=10))
        playlist_entry = (await get_player()).playlist_entry
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
        self, playlist_provider, get_player, communicator
    ):
        """Test that a new song is requested to play when the player is ready.

        There are playlist entries awaiting to be played.
        """
        player = await get_player()
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
        self, playlist_provider, get_player, communicator
    ):
        """Test that idle screen is requested to play when the player is ready.

        The playlist is empty.
        """
        # empty the playlist
        await database_sync_to_async(
            lambda: models.PlaylistEntry.objects.all().delete()
        )()

        player = await get_player()
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

    async def test_send_playlist_entry(
        self, playlist_provider, communicator, get_karaoke, get_player
    ):
        """Test to send a new playlist entry to the device."""
        player = await get_player()

        # pre assert
        assert playlist_provider.pe1.date_played is None

        karaoke = await get_karaoke()

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
        player_new = await get_player()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_playlist_entry_failed_none(
        self, communicator, get_karaoke, get_player
    ):
        """Test a null playlist entry cannot be sent to the device."""
        player = await get_player()

        # pre assert
        assert player.playlist_entry is None

        karaoke = await get_karaoke()

        # call the method
        await channel_layer.send(
            karaoke.channel_name,
            {"type": "send_playlist_entry", "playlist_entry": None},
        )

        # wait the outcoming event
        with pytest.raises(ValueError):
            await communicator.wait()

        # assert there are no side effects
        player_new = await get_player()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # no need to close connection

    async def test_send_idle(
        self, playlist_provider, communicator, get_karaoke, get_player
    ):
        """Test to send a new playlist entry to the device."""
        karaoke = await get_karaoke()
        player = await get_player()

        # call the method
        await channel_layer.send(karaoke.channel_name, {"type": "send_idle"})

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "idle"

        # assert there are no side effects
        player_new = await get_player()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_pause(
        self, playlist_provider, communicator, get_karaoke, get_player
    ):
        """Test to send to the player a pause command."""
        karaoke = await get_karaoke()
        player = await get_player()

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
        player_new = await get_player()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_play(
        self, playlist_provider, communicator, get_karaoke, get_player
    ):
        """Test to send to the player a play command."""
        karaoke = await get_karaoke()
        player = await get_player()

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
        player_new = await get_player()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_skip(
        self, playlist_provider, communicator, get_karaoke, get_player
    ):
        """Test to send to the player a skip command."""
        karaoke = await get_karaoke()
        player = await get_player()

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
        player_new = await get_player()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_command_unknown_failed(
        self, communicator, get_karaoke, get_player
    ):
        """Test an invalid command cannot be sent to the player."""
        karaoke = await get_karaoke()
        player = await get_player()

        # call the method
        await channel_layer.send(
            karaoke.channel_name, {"type": "send_command", "command": "unknown"}
        )

        # wait the outcoming event
        with pytest.raises(ValueError):
            await communicator.wait()

        # assert there are no side effects
        player_new = await get_player()
        assert player_new == player

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # no need to close connection

    async def test_send_handle_next(
        self,
        playlist_provider,
        communicator,
        client_drf,
        mocker,
        get_karaoke,
        get_player,
        get_player_token,
    ):
        """Test to handle next playlist entries untill the end of the playlist."""
        # configure HTTP client
        url = reverse("playlist-player-status")

        # mock the broadcaster
        # we cannot call it within an asynchronous test
        mocker.patch("playlist.views.send_to_channel")
        # mocked_send_to_channel = mocker.patch("playlist.views.send_to_channel")

        # create player and token
        player = await get_player()
        token = await get_player_token()

        # assert kara is ongoing and player play next song
        karaoke = await get_karaoke()
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
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        response = client_drf.put(
            url,
            data={
                "event": "started_song",
                "playlist_entry_id": playlist_provider.pe1.id,
            },
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player = await get_player()
        assert player.playlist_entry == playlist_provider.pe1

        # # assert the front has been notified
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

        # notify the first playlist entry has finished
        response = client_drf.put(
            url,
            data={"event": "finished", "playlist_entry_id": playlist_provider.pe1.id},
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player = await get_player()
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
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        response = client_drf.put(
            url,
            data={
                "event": "started_song",
                "playlist_entry_id": playlist_provider.pe2.id,
            },
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player = await get_player()
        assert player.playlist_entry == playlist_provider.pe2

        # notify the second playlist entry has finished
        response = client_drf.put(
            url,
            data={"event": "finished", "playlist_entry_id": playlist_provider.pe2.id},
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player = await get_player()
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

    async def test_send_handle_next_pause_skip(
        self,
        playlist_provider,
        communicator,
        client_drf,
        mocker,
        get_karaoke,
        get_player,
        get_player_token,
    ):
        """Test to handle next playlist entries then pause then skip."""
        # configure HTTP client
        url = reverse("playlist-player-status")

        # mock the broadcaster
        # we cannot call it within an asynchronous test
        mocker.patch("playlist.views.send_to_channel")

        # get player and token
        player = await get_player()
        token = await get_player_token()

        # assert player is currently idle
        assert player.playlist_entry is None

        # play the first playlist entry
        karaoke = await get_karaoke()
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
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        response = client_drf.put(
            url,
            data={
                "event": "started_song",
                "playlist_entry_id": playlist_provider.pe1.id,
            },
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player = await get_player()
        assert player.playlist_entry == playlist_provider.pe1

        # pause the player
        await channel_layer.send(
            karaoke.channel_name, {"type": "send_command", "command": "pause"}
        )

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "command"
        assert event["data"]["command"] == "pause"

        # notify the player is paused
        response = client_drf.put(
            url,
            data={
                "event": "paused",
                "playlist_entry_id": playlist_provider.pe1.id,
                "timing": 2,
            },
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player = await get_player()
        assert player.paused

        # skip the current playlist entry
        await channel_layer.send(
            karaoke.channel_name, {"type": "send_command", "command": "skip"}
        )

        # wait the outcoming event
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "command"
        assert event["data"]["command"] == "skip"

        # notify the first playlist entry has finished
        response = client_drf.put(
            url,
            data={"event": "finished", "playlist_entry_id": playlist_provider.pe1.id},
            HTTP_AUTHORIZATION="Token " + token,
        )

        assert response.status_code == status.HTTP_200_OK

        # assert the player has been updated
        player2 = await get_player()
        assert player2.playlist_entry is None
        assert not player2.paused

        # play the second playlist entry
        await channel_layer.send(karaoke.channel_name, {"type": "handle_next"})

        # wait for the event of the second playlist entry to play
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "playlist_entry"
        assert event["data"]["id"] == playlist_provider.pe2.id

        # close connection
        await communicator.disconnect()

    async def test_send_handle_next_karaoke_not_ongoing(
        self, playlist_provider, communicator, get_karaoke, get_player
    ):
        """Test to handle next playlist entries when the karaoke is not ongoing."""
        # set the karaoke not ongoing
        await database_sync_to_async(
            lambda: playlist_provider.set_karaoke(ongoing=False)
        )()

        # create karaoke and player
        karaoke = await get_karaoke()
        player = await get_player()

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
        player_new = await get_player()
        assert player == player_new

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_send_handle_next_karaoke_not_play_next_song(
        self, playlist_provider, communicator, get_karaoke, get_player, get_player_token
    ):
        """Test to handle next playlist entries when the player does not play
        next song."""
        # set player does not play next song
        await database_sync_to_async(
            lambda: playlist_provider.set_karaoke(player_play_next_song=False)
        )()

        # create karaoke and player
        karaoke = await get_karaoke()
        player = await get_player()

        # assert player is currently idle
        assert player.playlist_entry is None

        # there should not be anything to play for now
        await channel_layer.send(karaoke.channel_name, {"type": "handle_next"})

        # wait for the event of idle
        event = await communicator.receive_json_from()

        # assert the event
        assert event["type"] == "idle"

        # assert the player has not changed
        player_new = await get_player()
        assert player == player_new

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done

        # close connection
        await communicator.disconnect()

    async def test_connect_reset_playing_playlist_entry(
        self, playlist_provider, get_player, get_player_token
    ):
        """Test to reset playing playlist entry when connecting."""
        token = await get_player_token()
        communicator = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator.scope["headers"].append(
            (b"authorization", ("Token " + token).encode())
        )
        connected, _ = await communicator.connect()

        # set player playing
        await database_sync_to_async(
            lambda: playlist_provider.player_play_next_song()
        )()
        player = await get_player()
        assert player.playlist_entry is not None

        # disconnect and reconnect the player
        await communicator.disconnect()
        communicator_new = WebsocketCommunicator(application, "/ws/playlist/device/")
        communicator_new.scope["headers"].append(
            (b"authorization", ("Token " + token).encode())
        )
        connected, _ = await communicator_new.connect()

        # check that the player is idle
        player_new = await get_player()
        assert player_new.playlist_entry is None

        await communicator_new.disconnect()

    async def test_disconnect_player_while_playing(
        self, playlist_provider, communicator, get_player
    ):
        """Test that current playlist entry is reseted when player is disconnected."""
        # start playing a song
        await database_sync_to_async(
            lambda: playlist_provider.player_play_next_song(timing=timedelta(seconds=1))
        )()
        player = await get_player()
        assert player.playlist_entry == playlist_provider.pe1

        # stop the player connection
        await communicator.disconnect()

        # assert the play is stopped
        player = await get_player()
        assert player.playlist_entry is None
        assert player.timing == timedelta()

        # check there are no other messages
        done = await communicator.receive_nothing()
        assert done
