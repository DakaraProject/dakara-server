from datetime import timedelta

import pytest
from async_generator import yield_, async_generator  # needed for Python 3.5
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from rest_framework.authtoken.models import Token

from dakara_server.routing import application
from playlist.consumers import PlaylistDeviceConsumer
from playlist import models

channel_layer = get_channel_layer()


@pytest.fixture
@async_generator
async def communicator(provider):
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer,
                                         "/ws/playlist/device/")
    communicator.scope['user'] = provider.player
    connected, _ = await communicator.connect()

    assert connected

    await yield_(communicator)

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authentication(provider):
    # create a token
    token = Token.objects.create(user=provider.player)
    headers = [
        (b'authorization', "Token {}".format(token.key).encode()),
        (b'origin', b"localhost"),
    ]

    communicator = WebsocketCommunicator(application, "/ws/playlist/device/",
                                         headers=headers)
    connected, _ = await communicator.connect()

    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authenticate_player_successful(provider):
    """Test to authenticate as a player
    """
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer,
                                         "/ws/playlist/device/")
    communicator.scope['user'] = provider.player
    connected, _ = await communicator.connect()

    assert connected
    await communicator.disconnect()


# @pytest.mark.asyncio
# @pytest.mark.django_db(transaction=True)
# async def test_authenticate_player_twice_failed(provider):
#     """Test to authenticate two players successively
#     """
#     # authenticate first player
#     communicator_first = WebsocketCommunicator(PlaylistDeviceConsumer,
#                                                "/ws/playlist/device/")
#     communicator_first.scope['user'] = provider.player
#     connected, _ = await communicator_first.connect()
#
#     assert connected
#     await communicator_first.disconnect()
#
#     # authenticate second player
#     communicator_second = WebsocketCommunicator(PlaylistDeviceConsumer,
#                                                 "/ws/playlist/device/")
#     communicator_second.scope['user'] = provider.player
#     connected, _ = await communicator_second.connect()
#
#     assert not connected
#     await communicator_second.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authenticate_user_failed(provider):
    """Test to authenticate as a normal user
    """
    communicator = WebsocketCommunicator(PlaylistDeviceConsumer,
                                         "/ws/playlist/device/")
    communicator.scope['user'] = provider.user
    connected, _ = await communicator.connect()

    assert not connected
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_receive_ready_send_playlist_entry(provider, player,
                                                 communicator):
    """Test that a new song is requested to play when the player is ready

    There are playlist entries awaiting to be played.
    """
    assert player.playlist_entry is None

    # send the event
    await communicator.send_json_to({
        'type': 'ready'
    })

    # get the new song event
    event = await communicator.receive_json_from()
    assert event['type'] == 'playlist_entry'
    assert event['data']['id'] == provider.pe1.id

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_receive_ready_send_idle(provider, player, communicator):
    """Test that idle screen is requested to play when the player is ready

    The playlist is empty.
    """
    # empty the playlist
    models.PlaylistEntry.objects.all().delete()

    assert player.playlist_entry is None

    # send the event
    await communicator.send_json_to({
        'type': 'ready'
    })

    # get the new song event
    event = await communicator.receive_json_from()
    assert event['type'] == 'idle'

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_playlist_entry(provider, player, communicator, mocker):
    """Test to send a new playlist entry to the device
    """
    mocked_broadcast_to_channel = mocker.patch(
        'playlist.consumers.broadcast_to_channel')

    # pre assert
    assert provider.pe1.date_played is None

    # call the method
    await channel_layer.group_send('playlist.device', {
        'type': 'send_playlist_entry',
        'playlist_entry': provider.pe1
    })

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'playlist_entry'
    assert event['data']['id'] == provider.pe1.id

    # assert the side effects
    pe1 = models.PlaylistEntry.objects.get(pk=provider.pe1.id)
    assert pe1.date_played is not None
    player = models.Player.get_or_create()
    assert player.playlist_entry == pe1
    assert player.timing == timedelta(0)
    assert player.in_transition
    assert not player.paused
    mocked_broadcast_to_channel.assert_called_with(
        'playlist.front',
        'send_player_playlist_entry',
        {'playlist_entry': pe1}
    )

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_idle(provider, player, communicator, mocker):
    """Test to send a new playlist entry to the device
    """
    # mock the broadcast command
    mocked_broadcast_to_channel = mocker.patch(
        'playlist.consumers.broadcast_to_channel')

    # call the method
    await channel_layer.group_send('playlist.device', {
        'type': 'send_idle'
    })

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'idle'

    # assert the side effects
    player = models.Player.get_or_create()
    assert player.playlist_entry is None
    assert player.timing == timedelta(0)
    assert not player.in_transition
    assert not player.paused
    mocked_broadcast_to_channel.assert_called_with(
        'playlist.front',
        'send_player_idle',
    )

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_status_request(communicator):
    """Test to send a status request
    """
    # call the method
    await channel_layer.group_send('playlist.device', {
        'type': 'send_status_request'
    })

    # wait the outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'status_request'

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_command_pause(provider, player, communicator):
    """Test to send to the player a pause command
    """
    # call the method
    await channel_layer.group_send('playlist.device', {
        'type': 'send_command',
        'command': 'pause'
    })

    # wait the first outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'command'
    assert event['data']['command'] == 'pause'

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # wait the second outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'status_request'

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_command_play(provider, player, communicator):
    """Test to send to the player a play command
    """

    # call the method
    await channel_layer.group_send('playlist.device', {
        'type': 'send_command',
        'command': 'play'
    })

    # wait the first outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'command'
    assert event['data']['command'] == 'play'

    # assert there are no side effects
    player_new = models.Player.get_or_create()
    assert player_new == player

    # wait the second outcoming event
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'status_request'

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_handle_next(provider, player, communicator):
    """Test to handle next playlist entries untill the end of the playlist
    """
    # assert kara status is in play mode
    karaoke = models.Karaoke.get_object()
    assert karaoke.status == models.Karaoke.PLAY

    # assert player is currently idle
    assert player.playlist_entry is None

    # play the first playlist entry
    await channel_layer.group_send('playlist.device', {
        'type': 'handle_next'
    })

    # wait for the event of the first playlist entry to play
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'playlist_entry'
    assert event['data']['id'] == provider.pe1.id

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry == provider.pe1

    # mark the first playlist entry as played
    provider.pe1.was_played = True
    provider.pe1.save()

    # play the second playlist entry
    await channel_layer.group_send('playlist.device', {
        'type': 'handle_next'
    })

    # wait for the event of the second playlist entry to play
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'playlist_entry'
    assert event['data']['id'] == provider.pe2.id

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry == provider.pe2

    # mark the second playlist entry as played
    provider.pe2.was_played = True
    provider.pe2.save()

    # now the playlist should be empty
    await channel_layer.group_send('playlist.device', {
        'type': 'handle_next'
    })

    # wait for the event of idle
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'idle'

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry is None

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_handle_next_karaoke_stop(provider, player,
                                             communicator):
    """Test to handle next playlist entries when the karaoke is stopped
    """
    # set the kara status in stop mode
    karaoke = models.Karaoke.get_object()
    karaoke.status = models.Karaoke.STOP
    models.PlaylistEntry.objects.all().delete()
    karaoke.save()

    # assert player is currently idle
    assert player.playlist_entry is None

    # the playlist should be empty
    await channel_layer.group_send('playlist.device', {
        'type': 'handle_next'
    })

    # wait for the event of idle
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'idle'

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry is None

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_send_handle_next_karaoke_pause(provider, player,
                                              communicator):
    """Test to handle next playlist entries when the karaoke is paused
    """
    # set the kara status in pause mode
    karaoke = models.Karaoke.get_object()
    karaoke.status = models.Karaoke.PAUSE
    karaoke.save()

    # assert player is currently idle
    assert player.playlist_entry is None

    # there should not be anything to play for now
    await channel_layer.group_send('playlist.device', {
        'type': 'handle_next'
    })

    # wait for the event of idle
    event = await communicator.receive_json_from()

    # assert the event
    assert event['type'] == 'idle'

    # assert the player has been updated
    player = models.Player.get_or_create()
    assert player.playlist_entry is None

    # check there are no other messages
    done = await communicator.receive_nothing()
    assert done
