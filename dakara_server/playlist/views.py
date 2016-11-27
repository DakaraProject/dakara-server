from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, \
                                    ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from playlist.models import PlaylistEntry, Player, PlayerCommand
from playlist.serializers import PlaylistEntrySerializer, \
                                 PlaylistEntryReadSerializer, \
                                 PlaylistEntryForPlayerSerializer, \
                                 PlayerSerializer, \
                                 PlayerDetailsSerializer, \
                                 PlayerCommandSerializer, \
                                 PlayerErrorSerializer, \
                                 PlayerErrorsPoolSerializer
import logging

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

    def destroy(self, request, *args, **kwargs):
        playing_id = get_player().playlist_entry_id
        instance = self.get_object()
        if playing_id == instance.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlaylistEntryList(ListCreateAPIView):
    """ Class for listing or creating new entry in the playlist
    """
    serializer_class = PlaylistEntrySerializer
    pagination_class = PlaylistEntryPagination

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return PlaylistEntrySerializer

        return PlaylistEntryReadSerializer

    def get_queryset(self):
        player = get_player()
        entry_id = player.playlist_entry_id
        return PlaylistEntry.objects.exclude(pk=entry_id) \
            .order_by('date_created')


class PlayerCommandForUserView(APIView):
    """ Class for the user to view or send commands
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Get pause or skip status
        """
        player_command = get_player_command()
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
                cache.set('player_command', player_command)
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


class PlayerForUserView(APIView):
    """ Class for user to get the player stiatus
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Get player status
            Create one if it doesn't exist
        """
        player = get_player()
        serializer = PlayerDetailsSerializer(
                player,
                context={'request': request}
                )
        return Response(
                serializer.data,
                status.HTTP_200_OK
                )


class PlayerForPlayerView(APIView):
    """ Class for the player to communicate with the server

        Recieve status from player
        Send commands to player
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Get next playist entry
        """
        player = get_player()
        entry = get_next_playlist_entry(player.playlist_entry_id)
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
            player_command = get_player_command()
            player_old = get_player()
            player = Player(**player_serializer.validated_data)
            try:
                playing_old_id = player_old.playlist_entry_id
                playing_id = player.playlist_entry_id
                next_entry = get_next_playlist_entry(playing_old_id)
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
                            cache.set('player_command', player_command)

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
                    cache.set('player', player)

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
                        message = 'ERROR Player is not supposed to do that'
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


class PlayerErrorsForUserView(APIView):
    """ Class to send player errors pool
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Send player error pool
        """
        player_errors_pool = get_player_errors_pool()
        serializer = PlayerErrorsPoolSerializer(
                player_errors_pool,
                many=True,
                context={'request': request}
                )
        return Response(
                serializer.data,
                status.HTTP_200_OK
                )


class PlayerErrorForPlayerView(APIView):
    """ Class to handle player errors
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """ Recieve error message, log it, keep it in cache and delete
            entry from playlist

            The error can happen at the middle of the song, or at its
            very beginning. In that case, the player may have had no
            time to actualize its status to the server
        """
        player_error = PlayerErrorSerializer(data=request.data)

        if player_error.is_valid():
            player = get_player()
            entry_id_error = player_error.validated_data['playlist_entry']
            entry_id_current = player.playlist_entry_id
            entry_next = get_next_playlist_entry(entry_id_current)
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
            player_errors_pool = get_player_errors_pool()
            player_errors_count = get_player_errors_count()
            player_errors_pool.append({
                'id': player_errors_count,
                'song': error_song,
                'error_message': player_error.validated_data['error_message'],
                })
            cache.set('player_errors_pool', player_errors_pool, 10)
            cache.incr('player_errors_count')


            return Response(
                    status=status.HTTP_200_OK
                    )
        return Response(
                player_error.errors,
                status=status.HTTP_400_BAD_REQUEST
                )


##
# Routines
#


def get_next_playlist_entry(id):
    """ Returns the next playlist_entry in playlist
        excluding entry with specified id
    """
    playlist = PlaylistEntry.objects.exclude(pk=id).order_by('date_created')
    if not playlist:
        return None
    playlist_entry = playlist[0]
    return playlist_entry


def get_player():
    """ Load or create a new player
    """
    player = cache.get('player')
    if player is None:
        player = Player()
    return player


def get_player_command():
    """ Load or create a new player command
    """
    player_command = cache.get('player_command')
    if player_command is None:
        player_command = PlayerCommand()
    return player_command


def get_player_errors_count():
    """ Load or create a new count for player errors
    """
    count = cache.get('player_errors_count')
    if count is None:
        count = 0
        cache.set('player_errors_count', 0)
    return count


def get_player_errors_pool():
    """ Load or create a new pool for player errors
    """
    pool = cache.get('player_errors_pool')
    if pool is None:
        pool = []
    return pool
