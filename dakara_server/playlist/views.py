from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, \
                                    ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from playlist.models import PlaylistEntry, Player, PlayerCommand, PlayerErrorsPool
from playlist.serializers import (
        PlaylistEntrySerializer,
        PlaylistEntryReadSerializer,
        PlaylistEntryForPlayerSerializer,
        PlayerSerializer,
        PlayerDetailsSerializer,
        PlayerCommandSerializer,
        PlayerErrorSerializer,
        PlayerErrorsPoolSerializer,
        PlayerDetailsCommandErrorsSerializer,
        )

import logging

from . import permissions

# logger object
logger = logging.getLogger(__name__)


class PlaylistEntryPagination(PageNumberPagination):
    """ Class for pagination setup for playlist entries
    """
    page_size = 100


class PlaylistEntryDetail(RetrieveUpdateDestroyAPIView):
    """ Class for editing an playlist entry
    """
    queryset = PlaylistEntry.objects.all()
    serializer_class = PlaylistEntrySerializer
    permission_classes = [
            permissions.IsPlaylistManagerOrOwnerOrReadOnly
            ]

    def destroy(self, request, *args, **kwargs):
        playing_id = Player.get_or_create().playlist_entry_id
        instance = self.get_object()
        if playing_id == instance.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


##
# Playlist view for front
#


class PlaylistEntryList(ListCreateAPIView):
    """ Class for listing or creating new entry in the playlist
    """
    pagination_class = PlaylistEntryPagination
    permission_classes = [
            permissions.IsPlaylistUserOrReadOnly
            ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return PlaylistEntrySerializer

        return PlaylistEntryReadSerializer

    def get_queryset(self):
        player = Player.get_or_create()
        entry_id = player.playlist_entry_id
        return PlaylistEntry.objects.exclude(pk=entry_id) \
            .order_by('date_created')


##
# Player views for user
#


class PlayerForUserView(APIView):
    """ Class for user to get the player status
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Get player status
            Create one if it doesn't exist
        """
        player = Player.get_or_create()
        serializer = PlayerDetailsSerializer(
                player,
                context={'request': request}
                )

        return Response(
                serializer.data,
                status.HTTP_200_OK
                )


class PlayerCommandForUserView(APIView):
    """ Class for the user to view or send commands
    """
    permission_classes = [
            permissions.IsPlaylistManagerOrPlayingEntryOwnerOrReadOnly
            ]

    def get(self, request):
        """ Get pause or skip status
        """
        player_command = PlayerCommand.get_or_create()
        serializer = PlayerCommandSerializer(player_command)

        return Response(
                serializer.data,
                status.HTTP_200_OK
                )

    def put(self, request):
        """ Send pause or skip requests
        """
        serializer = PlayerCommandSerializer(data=request.data)
        try:
            if serializer.is_valid():
                player_command = PlayerCommand(**serializer.data)
                player_command.save()

                return Response(
                        serializer.data,
                        status.HTTP_202_ACCEPTED
                        )

            return Response(
                    serializer.errors,
                    status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            print(e)
            raise


class PlayerErrorsForUserView(APIView):
    """ Class to send player errors pool
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Send player error pool
        """
        player_errors_pool = PlayerErrorsPool.get_or_create()
        serializer = PlayerErrorsPoolSerializer(
                player_errors_pool.dump(),
                many=True,
                context={'request': request}
                )

        return Response(
                serializer.data,
                status.HTTP_200_OK
                )


class PlayerDetailsCommandErrorsForUserView(APIView):
    """ Class to send aggregated player status
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Send aggregated player status 
        """
        # Get player
        player = Player.get_or_create()

        # Get player commands
        player_command = PlayerCommand.get_or_create()

        # Get player errors
        player_errors_pool = PlayerErrorsPool.get_or_create()

        serializer = PlayerDetailsCommandErrorsSerializer(
                {
                    "status": player,
                    "manage": player_command,
                    "errors": player_errors_pool.dump(),
                },
                context={'request': request},
            )

        return Response(
                serializer.data,
                status.HTTP_200_OK
                )


##
# Player views for player
#


class PlayerForPlayerView(APIView):
    """ Class for the player to communicate with the server

        Recieve status from player
        Send commands to player
    """
    permission_classes = [
            permissions.IsPlayer
            ]

    def get(self, request):
        """ Get next playist entry
        """
        player = Player.get_or_create()
        entry = PlaylistEntry.get_next(player.playlist_entry_id)
        serializer = PlaylistEntryForPlayerSerializer(entry)
        return Response(
                serializer.data,
                status.HTTP_200_OK
                )

    def put(self, request):
        """ Send commands on recieveing status
        """
        player_serializer = PlayerSerializer(
                data=request.data
                )

        if player_serializer.is_valid():
            player_command = PlayerCommand.get_or_create()
            player_old = Player.get_or_create()
            player = Player(**player_serializer.validated_data)
            try:
                playing_old_id = player_old.playlist_entry_id
                playing_id = player.playlist_entry_id
                next_entry = PlaylistEntry.get_next(playing_old_id)
                next_id = next_entry.id if next_entry else None

                # check player status is consistent
                # playing entry has to be either same as before,
                # or the value returned by get_next_song
                if playing_old_id == playing_id or playing_id == next_id:

                    # if we're playing something new
                    if playing_id != playing_old_id:

                        # reset skip flag if present
                        if player_command.skip:
                            player_command.skip = False
                            player_command.save()

                        # remove previous entry from playlist if there was any
                        if playing_old_id:
                            PlaylistEntry.objects.get(
                                    id=playing_old_id
                                    ).delete()

                        if player.playlist_entry_id:
                            logger.info(
                                "INFO The player has started {song}".format(
                                    song=PlaylistEntry.objects.get(
                                        id=player.playlist_entry_id
                                        )
                                    )
                                )

                        else:
                            logger.info("INFO The player has stopped playing")

                    # save new player
                    player.save()

                    # Send commands to the player
                    player_command_serializer = PlayerCommandSerializer(
                            player_command
                            )

                    return Response(
                            player_command_serializer.data,
                            status=status.HTTP_202_ACCEPTED
                            )

                else:
                        # TODO the player is not doing what it's supposed to do
                        message = r"""ERROR Player is not supposed to do that,
                                      is playing {playing} but should be playing
                                      {old} or {next}""".format(
                                                  playing=playing_id,
                                                  old=playing_old_id,
                                                  next=next_id)
                        logger.error(message)
                        raise Exception(message)

            except Exception:
                logger.exception('EXCEPTION Unexpected error')
                raise

        # if invalid data from the player
        return Response(
                player_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )


class PlayerErrorForPlayerView(APIView):
    """ Class to handle player errors
    """
    permission_classes = [
            permissions.IsPlayer
            ]

    def post(self, request):
        """ Recieve error message, log it, keep it in cache and delete
            entry from playlist

            The error can happen at the middle of the song, or at its
            very beginning. In that case, the player may have had no
            time to actualize its status to the server
        """
        player_error = PlayerErrorSerializer(data=request.data)

        if player_error.is_valid():
            player = Player.get_or_create()
            entry_id_error = player_error.validated_data['playlist_entry']
            entry_id_current = player.playlist_entry_id
            entry_next = PlaylistEntry.get_next(entry_id_current)

            # protection if the erroneous song is the last one to play
            entry_id_next = entry_next.id if entry_next else None
            error_song=PlaylistEntry.objects.get(id=entry_id_error).song

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
                PlaylistEntry.objects.get(id=entry_id_next).delete()

            else:
                # TODO error
                message = 'ERROR Player is not supposed to do that'
                logger.error(message)
                raise Exception(message)

            # log the event
            logger.warning("WARNING Unable to play {song}, \
remove from playlist\n\
Error message: {error_message}".format(
                song=error_song,
                error_message=player_error.validated_data['error_message']
                ))

            # store the event in player error pool
            player_errors_pool = PlayerErrorsPool.get_or_create()
            player_errors_pool.add(
                    song=error_song,
                    error_message=player_error.validated_data['error_message']
                    )

            player_errors_pool.save()

            return Response(
                    status=status.HTTP_201_CREATED
                    )

        return Response(
                player_error.errors,
                status=status.HTTP_400_BAD_REQUEST
                )
