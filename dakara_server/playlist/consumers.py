import logging
from datetime import datetime

from django.utils import timezone
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

from playlist import serializers_device as serializers, models, permissions

tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)

WS_4400_BAD_REQUEST = 4400
WS_4401_UNAUTHORIZED = 4401
WS_4403_FORBIDDEN = 4403


class PlaylistDeviceConsumer(JsonWebsocketConsumer):
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

    def receive_json(self, event):
        """Receive all incoming events
        """
        # get the method name associated with the type
        method_name = "receive_{}".format(event['type'])
        if not hasattr(self, method_name):
            raise ValueError("Event of unknown type received '{}'"
                             .format(event['type']))

        # call the method
        getattr(self, method_name)(event.get('data'))

    def send_new_entry(self, event):
        """Send next playlist entry
        """
        entry = event['entry']

        if entry is None:
            raise ValueError("Entry must not be None")

        # Set `date_played` for new playlist entry
        entry.date_played = datetime.now(tz)
        entry.save()

        logger.info("The player will play '{song}'".format(song=entry.song))

        serializer = serializers.PlaylistEntrySerializer(entry)
        self.send_json({
            'type': 'new_entry',
            'data': serializer.data
        })

    def send_idle(self, event):
        """Request the player to be idle
        """
        logger.info("The player has nothing to play")
        self.send_json({
            'type': 'idle'
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
        command = event['command']
        if command not in ('play', 'pause'):
            raise ValueError("Unknown command requested '{}'"
                             .format(command))

        self.send_json({
            'type': 'command',
            'data': {
                'command': command
            }
        })

    def receive_entry_error(self, content):
        """Receive an error event from the player whin playing its entry
        """
        error_serializer = serializers.PlayerErrorSerializer(data=content)

        if not error_serializer.is_valid():
            self.close(code=WS_4400_BAD_REQUEST)
            logger.error("Entry error event invalid")
            return

        entry_id = error_serializer.validated_data['entry_id']
        entry = models.PlaylistEntry.objects.get(id=entry_id)
        song = entry.song

        # delete the entry from playlist
        entry.delete()

        # log the event
        logger.warning(
            (
                "Unable to play '{song}', "
                "remove from playlist, "
                "error message: '{error_message}'"
            ).format(
                song=song,
                error_message=error_serializer.validated_data['error_message']
            )
        )

        # store the event in player error pool
        player_errors_pool = models.PlayerErrorsPool.get_or_create()
        player_errors_pool.add(
            song=song,
            error_message=error_serializer.validated_data['error_message']
        )

        player_errors_pool.save()

        # continue the playlist
        self.handle_new_entry({'old_entry_id': entry_id})

    def receive_entry_finished(self, content):
        """Receive an event telling the player has finished to play its entry
        """
        entry_finished_serializer = serializers.PlayerEntryFinishedSerializer(
            data=content)

        if not entry_finished_serializer.is_valid():
            self.close(code=WS_4400_BAD_REQUEST)
            logger.error("Player finished entry event invalid")
            return

        # mark the entry as played
        entry_id = entry_finished_serializer.validated_data['entry_id']
        entry = models.PlaylistEntry.objects.get(id=entry_id)
        entry.was_played = True
        entry.save()

        # continue the playlist
        self.handle_new_entry({'old_entry_id': entry_id})

    def receive_status(self, content):
        """Receive player status

        Used only if a client wants to get the status right now.
        """
        status_serializer = serializers.PlayerStatusSerializer(
            data=content)

        if not status_serializer.is_valid():
            self.close(code=WS_4400_BAD_REQUEST)
            logger.error("Player status event invalid")
            return None

        logger.info("Received status: '{}'"
                    .format(status_serializer.validated_data))

        return status_serializer.validated_data

    def handle_new_entry(self, event):
        """Prepare the submission of a new entry depending on the context

        A new entry will be sent to the player if:
            - the kara status is in play mode;
            - there is a new entry in playlist after the provided one.
        """
        old_entry_id = event.get('old_entry_id')

        # get the next playlist entry if the kara is in play mode
        kara_status = models.KaraStatus.get_object()
        if kara_status.status != models.KaraStatus.PLAY:
            self.send_idle({})

        # get the new entry and request to play it
        entry = models.PlaylistEntry.get_next(old_entry_id)

        if entry is not None:
            self.send_new_entry({'entry': entry})

        else:
            self.send_idle({})
