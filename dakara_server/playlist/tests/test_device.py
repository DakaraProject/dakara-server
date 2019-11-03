import pytest
from async_generator import yield_, async_generator  # needed for Python 3.5
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from rest_framework import status
from django.core.urlresolvers import reverse
from datetime import timedelta

from dakara_server.routing import application
from playlist.consumers import PlaylistDeviceConsumer
from playlist import models

channel_layer = get_channel_layer()


@pytest.fixture
@async_generator
async def communicator(playlist_provider):
    """Gives a WebSockets communicator

    Use it for tests that does not raise errors.
    """
    # create a communicator
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer, "/ws/playlist/device/")

    # artificially give it a user
    communicator.scope["user"] = playlist_provider.player

    connected, _ = await communicator.connect()
    assert connected

    await yield_(communicator)

    await communicator.disconnect()


@pytest.fixture
@async_generator
async def communicator_open(playlist_provider):
    """Gives a WebSockets communicator that does not disconnect

    Use it for tests that raise errors.
    """
    # create a communicator
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer, "/ws/playlist/device/")

    # artificially give it a user
    communicator.scope["user"] = playlist_provider.player

    connected, _ = await communicator.connect()
    assert connected

    # give the communicator
    await yield_(communicator)

    # clean up
    await channel_layer.group_discard(
        communicator.instance.group_name, communicator.instance.channel_name
    )


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authentication(playlist_provider):
    """Test to authenticate with a token

    This is the normal mechanism of real-life connection. In the tests, we
    assume the user is already in the scope.
    """
    # create a token
    headers = []
    playlist_provider.authenticate(playlist_provider.player, headers=headers)

    communicator = WebsocketCommunicator(
        application, "/ws/playlist/device/", headers=headers
    )
    connected, _ = await communicator.connect()

    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authenticate_player_successful(playlist_provider):
    """Test to authenticate as a player
    """
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer, "/ws/playlist/device/")
    communicator.scope["user"] = playlist_provider.player
    connected, _ = await communicator.connect()

    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authenticate_player_twice_failed(playlist_provider):
    """Test to authenticate two players successively
    """
    # authenticate first player
    communicator_first = WebsocketCommunicator(
        PlaylistDeviceConsumer, "/ws/playlist/device/"
    )
    communicator_first.scope["user"] = playlist_provider.player
    connected, _ = await communicator_first.connect()

    assert connected

    # authenticate second player
    communicator_second = WebsocketCommunicator(
        PlaylistDeviceConsumer, "/ws/playlist/device/"
    )
    communicator_second.scope["user"] = playlist_provider.player
    connected, _ = await communicator_second.connect()

    assert not connected

    await communicator_first.disconnect()
    await communicator_second.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authenticate_user_failed(playlist_provider):
    """Test to authenticate as a normal user
    """
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer, "/ws/playlist/device/")
    communicator.scope["user"] = playlist_provider.user
    connected, _ = await communicator.connect()

    assert not connected
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_receive_ready_send_playlist_entry(
    playlist_provider, player, communicator
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


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_receive_ready_send_idle(playlist_provider, player, communicator):
    """Test that idle screen is requested to play when the player is ready

    The playlist is empty.
    """
    # empty the playlist
    models.PlaylistEntry.objects.all().delete()

    assert player.playlist_entry is None

    # send the event
    await communicator.send_json_to({"type": "ready"})

    # get the new song event
    event = await communicator.receive_json_from()
    assert event["type"] == "idle"

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_playlist_entry(playlist_provider, player, communicator):
    """Test to send a new playlist entry to the device
    """
    # pre assert
    assert playlist_provider.pe1.date_played is None

    # call the method
    await channel_layer.group_send(
        "playlist.device",
        {"type": "send_playlist_entry", "playlist_entry": playlist_provider.pe1},
    )

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "playlist_entry"
    assert event["data"]["id"] == playlist_provider.pe1.id

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_playlist_entry_failed_none(player, communicator_open):
    """Test a null playlist entry cannot be sent to the device
    """
    # pre assert
    assert player.playlist_entry is None

    # call the method
    await channel_layer.group_send(
        "playlist.device", {"type": "send_playlist_entry", "playlist_entry": None}
    )

    # wait the outcoming event
    with pytest.raises(ValueError):
        await communicator_open.wait()

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # check there are no other messages
    done = await communicator_open.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_idle(playlist_provider, player, communicator):
    """Test to send a new playlist entry to the device
    """
    # call the method
    await channel_layer.group_send("playlist.device", {"type": "send_idle"})

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "idle"

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_command_pause(playlist_provider, player, communicator):
    """Test to send to the player a pause command
    """
    # call the method
    await channel_layer.group_send(
        "playlist.device", {"type": "send_command", "command": "pause"}
    )

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "command"
    assert event["data"]["command"] == "pause"

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_command_play(playlist_provider, player, communicator):
    """Test to send to the player a play command
    """
    # call the method
    await channel_layer.group_send(
        "playlist.device", {"type": "send_command", "command": "play"}
    )

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "command"
    assert event["data"]["command"] == "play"

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_command_skip(playlist_provider, player, communicator):
    """Test to send to the player a skip command
    """
    # call the method
    await channel_layer.group_send(
        "playlist.device", {"type": "send_command", "command": "skip"}
    )

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "command"
    assert event["data"]["command"] == "skip"

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_command_failed(player, communicator_open):
    """Test an invalid command cannot be sent to the player
    """
    # call the method
    await channel_layer.group_send(
        "playlist.device", {"type": "send_command", "command": "unknown"}
    )

    # wait the outcoming event
    with pytest.raises(ValueError):
        await communicator_open.wait()

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # check there are no other messages
    done = await communicator_open.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_handle_next(playlist_provider, player, communicator, client_drf, mocker):
    """Test to handle next playlist entries untill the end of the playlist
    """
    # configure HTTP client
    url = reverse("playlist-player-status")
    playlist_provider.authenticate(playlist_provider.player, client=client_drf)

    # mock the broadcaster
    # we cannot call it within an asynchronous test
    mocked_broadcast_to_channel = mocker.patch("playlist.views.broadcast_to_channel")

    # assert kara is ongoing and player play next song
    karaoke = models.Karaoke.get_object()
    assert karaoke.ongoing
    assert karaoke.player_play_next_song

    # assert player is currently idle
    assert player.playlist_entry is None

    # play the first playlist entry
    await channel_layer.group_send("playlist.device", {"type": "handle_next"})

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
        data={"event": "started_song", "playlist_entry_id": playlist_provider.pe1.id},
    )

    assert response.status_code == status.HTTP_200_OK

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry == playlist_provider.pe1

    # assert the front has been notified
    mocked_broadcast_to_channel.assert_called_with(
        "playlist.front", "send_player_status", {"player": player}
    )

    # notify the first playlist entry has finished
    response = client_drf.put(
        url, data={"event": "finished", "playlist_entry_id": playlist_provider.pe1.id}
    )

    assert response.status_code == status.HTTP_200_OK

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry is None

    # play the second playlist entry
    await channel_layer.group_send("playlist.device", {"type": "handle_next"})

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
        data={"event": "started_song", "playlist_entry_id": playlist_provider.pe2.id},
    )

    assert response.status_code == status.HTTP_200_OK

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry == playlist_provider.pe2

    # notify the second playlist entry has finished
    response = client_drf.put(
        url, data={"event": "finished", "playlist_entry_id": playlist_provider.pe2.id}
    )

    assert response.status_code == status.HTTP_200_OK

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry is None

    # assert the front has been notified
    mocked_broadcast_to_channel.assert_called_with(
        "playlist.front", "send_player_status", {"player": player}
    )

    # now the playlist should be empty
    await channel_layer.group_send("playlist.device", {"type": "handle_next"})

    # wait for the event of idle
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "idle"

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_handle_next_karaoke_not_ongoing(
    playlist_provider, player, communicator
):
    """Test to handle next playlist entries when the karaoke is not ongoing
    """
    # set the karaoke not ongoing
    playlist_provider.set_karaoke(ongoing=False)

    # empty the playlist
    models.PlaylistEntry.objects.all().delete()

    # assert player is currently idle
    assert player.playlist_entry is None

    # the playlist should be empty
    await channel_layer.group_send("playlist.device", {"type": "handle_next"})

    # wait for the event of idle
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "idle"

    # assert the player has not changed
    player_new = models.Player.get_or_create()
    assert player == player_new

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_handle_next_karaoke_not_play_next_song(
    playlist_provider, player, communicator
):
    """Test to handle next playlist entries when the player does not play next song
    """
    # set player does not play next song
    playlist_provider.set_karaoke(player_play_next_song=False)

    # assert player is currently idle
    assert player.playlist_entry is None

    # there should not be anything to play for now
    await channel_layer.group_send("playlist.device", {"type": "handle_next"})

    # wait for the event of idle
    event = await communicator.receive_json_from()

    # assert the event
    assert event["type"] == "idle"

    # assert the player has not changed
    player_new = models.Player.get_or_create()
    assert player == player_new

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_connect_reset_playing_playlist_entry(playlist_provider, player):
    """Test to reset playing playlist entry
    """
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer, "/ws/playlist/device/")
    communicator.scope["user"] = playlist_provider.player
    connected, _ = await communicator.connect()

    # set player playing
    playlist_provider.player_play_next_song()
    assert player.playlist_entry is not None

    # disconnect and reconnect the player
    await communicator.disconnect()
    communicator2 = WebsocketCommunicator(
        PlaylistDeviceConsumer, "/ws/playlist/device/"
    )
    communicator2.scope["user"] = playlist_provider.player
    connected, _ = await communicator2.connect()

    # check that the player is idle
    player2 = models.Player.get_or_create()
    assert player2.playlist_entry is None

    await communicator2.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_disconnect_player_while_playing(
    playlist_provider, player, communicator_open
):
    """Test that current playlist entry is reseted when player is disconnected
    """
    # start playing a song
    playlist_provider.player_play_next_song(timing=timedelta(seconds=1))
    assert player.playlist_entry == playlist_provider.pe1

    # stop the player connection
    await communicator_open.disconnect()

    # assert the play is stopped
    assert player.playlist_entry is None
    assert player.timing == timedelta()

    # check there are no other messages
    done = await communicator_open.receive_nothing()
    assert done