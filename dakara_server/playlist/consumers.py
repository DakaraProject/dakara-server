import logging

from django.contrib.auth import get_user_model
from channels.generic.websocket import JsonWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from playlist import serializers, models

UserModel = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class DakaraJsonWebsocketConsumer(JsonWebsocketConsumer):
    """Custom consumer for the project

    On receive event, it wil call the corresponding method.
    """
    def receive_json(self, event):
        """Receive all incoming events and call the corresponding method
        """
        # get the method name associated with the type
        method_name = "receive_{}".format(event['type'])
        if not hasattr(self, method_name):
            # in this case, we do not raise an error, as this would reset the
            # websocket connexion
            logger.error("Event of unknown type received '{}'"
                         .format(event['type']))
            return

        # call the method
        getattr(self, method_name)(event.get('data'))


def broadcast_to_channel(group, method, data=None):
    """Send an event to a channel layer group

    Args:
        group (str): name of the group.
        method (str): name of the method.
        data (dict): data to pass to the method.
    """
    event = {'type': method}

    if data:
        event.update(data)

    async_to_sync(channel_layer.group_send)(group, event)


class PlaylistDeviceConsumer(DakaraJsonWebsocketConsumer):
    group_name = 'playlist.device'

    def connect(self):
        # the group must not exist before connection
        if self.group_name in self.channel_layer.groups:
            self.close()
            logger.error("Another player tries to connect to playlist "
                         "device consumer")
            return

        # ensure user is player
        if not \
           self.scope['user'].has_playlist_permission_level(UserModel.PLAYER):
            self.close()
            logger.error("Invalid user tries to connect to playlist "
                         "device consumer")
            return

        # create the group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )

        # reset current playing playlist entry if any
        current_playlist_entry = models.PlaylistEntry.get_playing()
        if current_playlist_entry is not None:
            current_playlist_entry.date_played = None
            current_playlist_entry.save()

        self.accept()
        logger.info("Player connected through websocket")

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

        # broadcast the player is idle
        broadcast_to_channel('playlist.front', 'send_player_idle')

    def receive_ready(self, event=None):
        """Start to play when the player is ready"""
        # request to start playing if possible
        logger.info("The player is ready")
        self.handle_next()

    def send_playlist_entry(self, event):
        """Send next playlist entry
        """
        playlist_entry = event['playlist_entry']

        if playlist_entry is None:
            raise ValueError("Playlist entry must not be None")

        # log the event
        logger.info("The player will play '{}'".format(playlist_entry))

        # send to device
        serializer = serializers.PlaylistEntryForPlayerSerializer(
            playlist_entry)
        self.send_json({
            'type': 'playlist_entry',
            'data': serializer.data
        })

    def send_idle(self, event=None):
        """Request the player to be idle
        """
        # log the event
        logger.info("The player will play idle screen")

        # send to device
        self.send_json({
            'type': 'idle'
        })

    def send_command(self, event):
        """Send a given command to the player
        """
        command = event['command']

        if command not in dict(models.Player.COMMANDS).keys():
            raise ValueError("Unknown command requested '{}'"
                             .format(command))

        logger.info("The player will {}".format(command))

        self.send_json({
            'type': 'command',
            'data': {
                'command': command
            }
        })

    def handle_next(self, event=None):
        """Prepare the submission of a new playlist entry depending on the context

        A new playlist entry will be sent to the player if:
            - the kara status is in play mode;
            - there is a new playlist entry in playlist after the provided one.
        """
        # get the next playlist entry if the kara is in play mode
        karaoke = models.Karaoke.get_object()
        if karaoke.status != models.Karaoke.PLAY:
            self.send_idle()
            return

        # get the new playlist_entry and request to play it
        playlist_entry = models.PlaylistEntry.get_next()

        if playlist_entry is not None:
            self.send_playlist_entry({'playlist_entry': playlist_entry})

        else:
            self.send_idle()
