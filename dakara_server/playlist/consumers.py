import logging

from django.contrib.auth import get_user_model
from channels.generic.websocket import JsonWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from playlist import serializers, models


UserModel = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class DispatchJsonWebsocketConsumer(JsonWebsocketConsumer):
    """Consumer that dispatch received JSON messages to methods

    On receive event, it will call the corresponding method based the event
    "type" key using the following pattern: "receive_{type}".
    """

    def receive_json(self, event):
        """Receive all incoming events and call the corresponding method
        """
        # get the method name associated with the type
        method_name = "receive_{}".format(event["type"])
        if not hasattr(self, method_name):
            # in this case, we do not raise an error, as this would reset the
            # websocket connexion
            logger.error("Event of unknown type received '%s'", event["type"])
            return

        # call the method
        getattr(self, method_name)(event.get("data"))


def send_to_channel(name, event_type, data=None):
    """Send an event to a channel

    Args:
        name (str): name of the channel.
        event_type (str): type of the event.
        data (dict): data to pass to the method.
    """
    # get channel name
    if name == PlaylistDeviceConsumer.name:
        channel_name = PlaylistDeviceConsumer.get_channel_name()

    else:
        raise UnknownConsumerError("Unknown consumer name requested '{}'".format(name))

    # if the channel does not exist, do nothing
    if channel_name is None:
        return

    # create event
    event = {"type": event_type}
    if data:
        event.update(data)

    # send event to channel
    async_to_sync(channel_layer.send)(channel_name, event)


class PlaylistDeviceConsumer(DispatchJsonWebsocketConsumer):
    """Consumer to handle device events
    """

    name = "playlist.device"

    @staticmethod
    def get_channel_name():
        """Retreive the channel name
        """
        karaoke = models.Karaoke.objects.get_object()
        return karaoke.channel_name

    def is_connected(self):
        """Tells if the consumer is connected
        """
        return self.get_channel_name() is not None

    def connect(self):
        # ensure user is connected
        if not isinstance(self.scope["user"], UserModel):
            logger.error(
                "Unauthenticated user tries to connect to playlist device consumer"
            )
            self.close()
            return

        # ensure user is player
        if not self.scope["user"].is_player:
            logger.error("Invalid user tries to connect to playlist device consumer")
            self.close()
            return

        # check if the channel is already connected
        if self.is_connected():
            logger.error("Another player tries to connect to playlist device consumer")
            self.close()
            return

        # reset current playing playlist entry if any
        current_playlist_entry = models.PlaylistEntry.objects.get_playing()
        if current_playlist_entry is not None:
            current_playlist_entry.date_played = None
            current_playlist_entry.save()

        # register the channel in database
        karaoke = models.Karaoke.objects.get_object()
        karaoke.channel_name = self.channel_name
        karaoke.save()

        # accept the connection
        self.accept()

        # log the connection
        logger.info("Player connected through websocket")

    def disconnect(self, close_code):
        # reset the current playing song if any
        entry = models.PlaylistEntry.objects.get_playing()
        if entry:
            entry.date_played = None
            entry.save()

        # set player idle
        karaoke = models.Karaoke.objects.get_object()
        models.Player.cache.create(id=karaoke.id)

        # unregister the channel in database
        karaoke = models.Karaoke.objects.get_object()
        karaoke.channel_name = None
        karaoke.save()

        # broadcast the player is idle
        # send_to_channel("playlist.front", "send_player_idle")

    def receive_ready(self, event=None):
        """Start to play when the player is ready
        """
        # request to start playing if possible
        logger.info("The player is ready")
        self.handle_next()

    def send_playlist_entry(self, event):
        """Send next playlist entry
        """
        playlist_entry = event["playlist_entry"]

        if playlist_entry is None:
            raise ValueError("Playlist entry must not be None")

        # log the event
        logger.info("The player will play '%s'", playlist_entry)

        # send to device
        serializer = serializers.PlaylistEntryForPlayerSerializer(playlist_entry)
        self.send_json({"type": "playlist_entry", "data": serializer.data})

    def send_idle(self, event=None):
        """Request the player to be idle
        """
        # log the event
        logger.info("The player will play idle screen")

        # send to device
        self.send_json({"type": "idle"})

    def send_command(self, event):
        """Send a given command to the player
        """
        command = event["command"]

        if command not in dict(models.Player.COMMANDS).keys():
            raise ValueError("Unknown command requested '{}'".format(command))

        logger.info("The player will %s", command)

        self.send_json({"type": "command", "data": {"command": command}})

    def handle_next(self, event=None):
        """Prepare the submission of a new playlist entry depending on the context

        A new playlist entry will be sent to the player if:
            - the karaoke is ongoing and set for player to play next song
            - there is a new playlist entry in playlist after the provided one.
        """
        # request to be idle if the kara is not ongoing
        # or player does not play next song
        karaoke = models.Karaoke.objects.get_object()
        if not (karaoke.ongoing and karaoke.player_play_next_song):
            self.send_idle()
            return

        # get the new playlist_entry and request to play it
        playlist_entry = models.PlaylistEntry.objects.get_next()

        if playlist_entry is not None:
            self.send_playlist_entry({"playlist_entry": playlist_entry})

        else:
            self.send_idle()


class UnknownConsumerError(Exception):
    """Error raised when trying to access a consumer whose name in unknown
    """
