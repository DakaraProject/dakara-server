import logging
from datetime import datetime

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

from playlist import serializers, models, permissions
from users.permissions import DummyRequest

tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)

WS_4400_BAD_REQUEST = 4400
WS_4401_UNAUTHORIZED = 4401
WS_4403_FORBIDDEN = 4403


class DakaraJsonWebsocketConsumer(JsonWebsocketConsumer):
    """Custom consumer for the project

    On receive event, it wil call the corresponding method.

    On send, it will add the current date and time.
    """
    def receive_json(self, event):
        """Receive all incoming events and call the corresponding method
        """
        # get the method name associated with the type
        method_name = "receive_{}".format(event['type'])
        if not hasattr(self, method_name):
            logger.error("Event of unknown type received '{}'"
                         .format(event['type']))
            return

        # call the method
        getattr(self, method_name)(event.get('data'))

    def send_json(self, content):
        """Add the date and time to the response"""
        serializer = serializers.AutoDateTimeSerializer({})
        content['date'] = serializer.data['date']

        return super().send_json(content)


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
        permission = permissions.IsPlayer()
        if not permission.has_permission(self.scope, None):
            self.close(code=WS_4403_FORBIDDEN)
            logger.error("Invalid user tries to connect to playlist "
                         "device consumer")
            return

        # create the group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )

        self.accept()

        # request to start playing if possible
        self.handle_new_entry({})

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

        # broadcast the player is idle
        async_to_sync(self.channel_layer.group_send)('playlist.front', {
            'type': 'send.device_idle'
        })

    def send_new_entry(self, event):
        """Send next playlist entry
        """
        entry = event['data']['entry']

        if entry is None:
            raise ValueError("Entry must not be None")

        # Set `date_played` for new playlist entry
        entry.date_played = datetime.now(tz)
        entry.save()

        logger.info("The player will play '{song}'".format(song=entry.song))

        serializer = serializers.PlaylistEntryForPlayerSerializer(entry)
        self.send_json({
            'type': 'new_entry',
            'data': serializer.data
        })

        # broadcast to the front
        async_to_sync(self.channel_layer.group_send)('playlist.front', {
            'type': 'send.device_new_entry',
            'data': {
                'entry': entry,
            }
        })

    def send_idle(self, event):
        """Request the player to be idle
        """
        logger.info("The player has nothing to play")
        self.send_json({
            'type': 'idle'
        })

        # broadcast to the front
        async_to_sync(self.channel_layer.group_send)('playlist.front', {
            'type': 'send.device_idle'
        })

    def send_status_request(self, event):
        """Request the player status
        """
        self.send_json({
            'type': 'status_request',
        })

    def send_command(self, event):
        """Send a given command to the player
        """
        command = event['data']['command']

        if command not in ('play', 'pause'):
            raise ValueError("Unknown command requested '{}'"
                             .format(command))

        logger.info("The player will {}".format(command))

        self.send_json({
            'type': 'command',
            'data': {
                'command': command
            }
        })

        # request status to broadcast it to the front
        self.send_status_request({})

    def receive_entry_error(self, content):
        """Receive an error event from the player whin playing its entry
        """
        serializer = serializers.PlayerErrorSerializer(data=content)

        if not serializer.is_valid():
            self.close(code=WS_4400_BAD_REQUEST)
            logger.error("Entry error event invalid")
            return

        entry = serializer.validated_data['entry']
        song = entry.song

        # mark the entry as played with error
        entry.was_played = True
        entry.had_error = True
        entry.save()

        # log the event
        logger.warning(
            (
                "Unable to play '{song}', "
                "remove from playlist, "
                "error message: '{message}'"
            ).format(
                song=song,
                message=serializer.validated_data['error_message']
            )
        )

        # store the event in player error pool
        player_errors_pool = models.PlayerErrorsPool.get_or_create()
        player_errors_pool.add(
            song=song,
            error_message=serializer.validated_data['error_message']
        )

        player_errors_pool.save()

        # broadcast the error to the front
        async_to_sync(self.channel_layer.group_send)('playlist.front', {
            'type': 'send.device_entry_error',
            'data': serializer.validated_data
        })

        # continue the playlist
        self.handle_new_entry({'data': {'old_entry_id': entry.id}})

    def receive_entry_finished(self, content):
        """Receive an event telling the player has finished to play its entry
        """
        serializer = serializers.PlayerEntryFinishedSerializer(
            data=content)

        if not serializer.is_valid():
            self.close(code=WS_4400_BAD_REQUEST)
            logger.error("Player finished entry event invalid")
            return

        # mark the entry as played
        entry = serializer.validated_data['entry']
        entry.was_played = True
        entry.save()

        # continue the playlist
        self.handle_new_entry({'data': {'old_entry_id': entry.id}})

    def receive_entry_started(self, content):
        """Receive an event telling the player has started to play its entry
        """
        serializer = serializers.PlayerEntryFinishedSerializer(
            data=content)

        if not serializer.is_valid():
            self.close(code=WS_4400_BAD_REQUEST)
            logger.error("Player finished entry event invalid")
            return

        # broadcast the information to the clients
        async_to_sync(self.channel_layer.group_send)('playlist.front', {
            'type': 'send_device_entry_started',
            'data': serializer.validated_data
        })

    def receive_status(self, content):
        """Receive player status

        Used only if a client wants to get the status right now.
        """
        serializer = serializers.PlayerStatusSerializer(
            data=content)

        if not serializer.is_valid():
            self.close(code=WS_4400_BAD_REQUEST)
            logger.error("Player status event invalid: {}".format(content))
            return

        if serializer.validated_data['entry'] is not None:
            logger.debug("The player is in {} for '{}' at {}".format(
                'pause' if serializer.validated_data['paused'] else 'play',
                serializer.validated_data['entry'].song,
                serializer.validated_data['timing']
            ))

        else:
            logger.debug("The player is idle")

        # broadcast to the front
        async_to_sync(self.channel_layer.group_send)('playlist.front', {
            'type': 'send.device_status',
            'data': serializer.validated_data
        })

    def handle_new_entry(self, event):
        """Prepare the submission of a new entry depending on the context

        A new entry will be sent to the player if:
            - the kara status is in play mode;
            - there is a new entry in playlist after the provided one.
        """
        if 'data' in event:
            old_entry_id = event['data']['old_entry_id']

        else:
            old_entry_id = None

        # get the next playlist entry if the kara is in play mode
        kara_status = models.KaraStatus.get_object()
        if kara_status.status != models.KaraStatus.PLAY:
            self.send_idle({})

        # get the new entry and request to play it
        entry = models.PlaylistEntry.get_next(old_entry_id)

        if entry is not None:
            self.send_new_entry({'data': {'entry': entry}})

        else:
            self.send_idle({})


class PlaylistFrontConsumer(DakaraJsonWebsocketConsumer):
    group_name = 'playlist.front'

    def connect(self):
        # ensure user is playlist user
        permission = IsAuthenticated()
        if not permission.has_permission(DummyRequest(**self.scope), None):
            self.close(code=WS_4403_FORBIDDEN)
            logger.error("Invalid user tries to connect to playlist "
                         "front consumer")
            return

        # create the group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )

        self.accept()

        # request status
        async_to_sync(self.channel_layer.group_send)('playlist.device', {
            'type': 'send.status_request'
        })

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

    def send_device_new_entry(self, event):
        """Tell the front the device is playing a new entry
        """
        entry = event['data']['entry']

        if entry is None:
            raise ValueError("Entry must not be None")

        serializer = serializers.PlaylistPlayedEntryWithDatePlayedSerializer(entry)

        logger.debug("Telling the front that the player is playing '{}'".
                     format(entry.song))

        self.send_json({
            'type': 'device_new_entry',
            'data': serializer.data
        })

    def send_device_idle(self, event):
        """Tell the front the device is idle
        """
        logger.debug("Telling the front that the player is idle")

        self.send_json({
            'type': 'device_idle'
        })

    def send_device_entry_error(self, event):
        """Tell the front the device had an error with an entry
        """
        entry = event['data']['entry']

        serializer = serializers.PlayerErrorSerializer(
            event['data'])

        logger.debug("Telling the front that the player had an error"
                     "when playing '{}'".format(entry.song))

        self.send_json({
            'type': 'device_entry_error',
            'data': serializer.data,
        })

    def send_device_entry_started(self, event):
        """Tell the front the device had started an entry
        """
        entry = event['data']['entry']

        serializer = serializers.PlaylistPlayedEntryWithDatePlayedSerializer(entry)

        logger.debug("Telling the front that the player has started to play"
                     "'{}'".format(entry.song))

        self.send_json({
            'type': 'device_entry_started',
            'data': serializer.data,
        })

    def send_device_status(self, event):
        """Send the status of the player
        """
        player_status = event['data']

        serializer = serializers.PlayerStatusSerializer(player_status)

        logger.debug("Sending the player status to the front")

        self.send_json({
            'type': 'device_status',
            'data': serializer.data
        })

    def send_kara_status(self, event):
        """Tell the front the updated kara status
        """
        if 'data' in event:
            kara_status = event['data']['kara_status']

        # if the kara status was not provided, request it
        else:
            kara_status = models.KaraStatus.get_object()

        serializer = serializers.KaraStatusSerializer(kara_status)

        logger.debug("Telling the front that the kara status is {}"
                     .format(kara_status))

        self.send_json({
            'type': 'kara_status',
            'data': serializer.data
        })

    def send_playlist_new_entry(self, event):
        """Tell the front a new entry has been added to the playlist
        """
        playlist, interval = models.PlaylistEntry.get_playlist_with_interval()
        entry = playlist[-1]

        serializer = serializers.PlaylistEntryWithIntervalEndSerializer({
            'entry': entry,
            'interval_end': interval
        })

        logger.debug("Telling the front that the playlist has a new "
                     "entry '{}'".format(entry.song))

        self.send_json({
            'type': 'playlist_new_entry',
            'data': serializer.data
        })

    def send_playlist(self, event):
        """Tell the front the current playlist

        It sends the complete playlist.
        """
        playlist, interval = models.PlaylistEntry.get_playlist_with_interval()

        serializer = serializers.PlaylistEntriesWithIntervalEndSerializer({
            'entries': playlist,
            'interval_end': interval,
        })

        logger.debug("Sending the playlist to the front")

        self.send_json({
            'type': 'playlist',
            'data': serializer.data
        })

    # def send_playlist_played(self, event):
    #     """Tell the front the current playlist of played entries
    #     """
    #     playlist = models.PlaylistEntry.get_playlist_played()
    #
    #     serializer = serializers.PlaylistPlayedEntryWithDatePlayedSerializer(
    #         playlist)
    #
    #     logger.debug("Sending the playlist of played entries to the front")
    #
    #     self.send_json({
    #         'type': 'playlist_played',
    #         'data': serializer.data
    #     })

    # def send_refresh(self, event):
    #     """Send the complete state of the kara
    #     """
    #     # request the player status and send it later
    #     async_to_sync(self.channel_layer.group_send)('playlist.device', {
    #         'type': 'send.status_request'
    #     })
    #
    #     # send the kara status
    #     self.send_kara_status({})
    #
    #     # send the playlist
    #     self.send_playlist({})
    #
    #     # send the played playlist
    #     self.send_playlist_played({})

    # def receive_refresh_request(self, content):
    #     """Receive a request to get the current state of the kara
    #     """
    #     logger.debug("Received request to refresh the state of the kara")
    #
    #     self.send_refresh({})
