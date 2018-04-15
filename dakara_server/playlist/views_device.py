import logging
from datetime import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models
from . import serializers
from . import permissions


tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)


class PlayerDeviceView(APIView):
    """Player to communicate status and commands of the player

    Recieve status from player
    Send commands to player
    """
    permission_classes = [
            permissions.IsPlayer
            ]

    def get(self, request):
        """Get next playist entry
        """
        player = models.Player.get_or_create()
        kara_status = models.KaraStatus.get_object()

        # get the next playlist entry if the kara is in play mode
        if kara_status.status == models.KaraStatus.PLAY:
            entry = models.PlaylistEntry.get_next(player.playlist_entry_id)

        else:
            entry = None

        serializer = serializers.PlaylistEntryForPlayerSerializer(entry)

        return Response(
                serializer.data,
                status.HTTP_200_OK
                )

    def put(self, request):
        """Send commands on recieveing status
        """
        player_serializer = serializers.PlayerSerializer(
                data=request.data
                )

        if not player_serializer.is_valid():
            return Response(
                    player_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                    )

        # skip the current playlist entry if the kara is in stop mode
        kara_status = models.KaraStatus.get_object()
        if kara_status.status == models.KaraStatus.STOP:
            player_command = models.PlayerCommand()
            player_command.skip = True

            # Send commands to the player
            player_command_serializer = serializers.PlayerCommandSerializer(
                    player_command
                    )

            return Response(
                    player_command_serializer.data,
                    status=status.HTTP_202_ACCEPTED
                    )

        player_command = models.PlayerCommand.get_or_create()
        player_old = models.Player.get_or_create()
        player = models.Player(**player_serializer.validated_data)

        playing_old_id = player_old.playlist_entry_id
        playing_id = player.playlist_entry_id
        next_entry = models.PlaylistEntry.get_next(playing_old_id)
        next_id = next_entry.id if next_entry else None

        # check player status is consistent
        # playing entry has to be either same as before,
        # or the value returned by get_next_song
        if not (
                playing_old_id == playing_id or
                playing_id == next_id or
                playing_id is None):
            raise RuntimeError("""Player is not supposed to do that, is playing
'{playing}' but should be playing '{old}' or '{next}'""".format(
                  playing=playing_id,
                  old=playing_old_id,
                  next=next_id
                  ))

        # if we're playing something new
        if playing_id != playing_old_id:

            # reset skip flag if present
            if player_command.skip:
                player_command.skip = False
                player_command.save()

            # mark previous entry from playlist as `played` if there was any
            if playing_old_id:
                previous_playlist_entry = models.PlaylistEntry.objects.get(
                        id=playing_old_id
                        )
                previous_playlist_entry.was_played = True
                previous_playlist_entry.save()

            if player.playlist_entry_id:
                # Set `date_played` for new playlist entry
                new_playlist_entry = models.PlaylistEntry.objects.get(
                        id=player.playlist_entry_id
                        )
                new_playlist_entry.date_played = datetime.now(tz)
                new_playlist_entry.save()

                logger.info(
                    "The player has started '{song}'".format(
                        song=new_playlist_entry.song)
                    )

            else:
                logger.info("The player has stopped playing")

        # save new player
        player.save()

        # Send commands to the player
        player_command_serializer = serializers.PlayerCommandSerializer(
                player_command
                )

        return Response(
                player_command_serializer.data,
                status=status.HTTP_202_ACCEPTED
                )


class PlayerDeviceErrorView(APIView):
    """Handle player errors
    """
    permission_classes = [
            permissions.IsPlayer
            ]

    def post(self, request):
        """Recieve error message, log it, keep it in cache and delete
        entry from playlist

        The error can happen at the middle of the song, or at its very
        beginning. In that case, the player may have had no time to actualize
        its status to the server.
        """
        player_error = serializers.PlayerErrorSerializer(data=request.data)

        if not player_error.is_valid():
            return Response(
                    player_error.errors,
                    status=status.HTTP_400_BAD_REQUEST
                    )

        player = models.Player.get_or_create()
        entry_id_error = player_error.validated_data['playlist_entry']
        entry_id_current = player.playlist_entry_id
        entry_next = models.PlaylistEntry.get_next(entry_id_current)

        # protection if the erroneous song is the last one to play
        entry_id_next = entry_next.id if entry_next else None
        error_song = models.PlaylistEntry.objects. \
            get(id=entry_id_error).song

        if entry_id_error == entry_id_current:
            # the server knows the player has already
            # started playing
            # Nothing to do
            pass

        elif entry_id_error == entry_id_next:
            # the server does not know the player has
            # started playing,
            # which means the error occured immediately and
            # status of the player has not been updated yet
            # remove the problematic song from the playlist
            models.PlaylistEntry.objects.get(id=entry_id_next).delete()

        else:
            raise RuntimeError("The player is not supposed to do that")

        # log the event
        logger.warning(
            """Unable to play '{song}', remove from playlist; error
message: {error_message}""".format(
                song=error_song,
                error_message=player_error.validated_data['error_message']
                ))

        # store the event in player error pool
        player_errors_pool = models.PlayerErrorsPool.get_or_create()
        player_errors_pool.add(
                song=error_song,
                error_message=player_error.validated_data['error_message']
                )

        player_errors_pool.save()

        return Response(
                status=status.HTTP_201_CREATED
                )
