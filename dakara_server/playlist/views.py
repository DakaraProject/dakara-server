from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from playlist.models import *
from playlist.serializers import *
from threading import Lock
import logging

# logger object
logger = logging.getLogger(__name__)
lock = Lock()


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
    queryset = PlaylistEntry.objects.all()
    serializer_class = PlaylistEntrySerializer
    pagination_class = PlaylistEntryPagination

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return PlaylistEntrySerializer 
        return PlaylistEntryReadSerializer



class PlayerCommandForUserView(APIView):
    """ Class for the user to view or send commands 
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Get playerCommand
            Create one if it doesn't exist
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
        player_command = get_player_command()
        serializer = PlayerCommandSerializer(player_command, data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()
                return Response(
                        serializer.data,
                        status.HTTP_202_ACCEPTED
                        )
            else:
                return Response(
                        serializer.errors,
                        status.HTTP_400_BAD_REQUEST
                        )
        except Exception as e:
            print(e)
            raise


class PlayerForUserView(APIView):
    """ Class for user to get the player status 
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Get player status
            Create one if it doesn't exist
        """
        player = get_player()
        serializer = PlayerDetailsSerializer(player, context={'request': request})
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
        
        player_command = get_player_command()
        player_old = get_player()
        entry_old = player_old.playlist_entry
        player_serializer = PlayerSerializer(
                player_old,
                data=request.data
                )
        if player_serializer.is_valid():
            player = Player(**player_serializer.validated_data)
            try:
                playing_old_id = entry_old.id if entry_old else None
                playing_id = player.playlist_entry.id if player.playlist_entry else None
                next_entry = get_next_playlist_entry(playing_old_id)
                next_id = next_entry.id if next_entry else None

                # check player status is consistent
                # playing entry has to be either same as before, or the value returned by get_next_song
                if playing_old_id == playing_id or playing_id == next_id:

                    #if we're playing something new                    
                    if playing_id != playing_old_id:

                        #reset skip flag if present
                        if player_command.skip:
                            player_command.skip = False
                            player_command.save()

                        #remove previous entry from playlist if there was any
                        if entry_old:
                            entry_old.delete()

                        if player.playlist_entry:
                            logger.info("INFO The player has started {song}".format(
                                song=player.playlist_entry.song
                                ))
                        else:
                            logger.info("INFO The player has stopped playing")

                    # save new player
                    player_serializer.save()

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

            except Exception as e:
                logger.exception('EXCEPTION Unexpected error')
                raise

        else:
            # if invalid data from the player
            return Response(
                    player_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                    )

class PlayerErrorView(APIView):
    """ Class to handle player errors
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """ Recieve error message, log it and delete entry from playlist

            The error can happen at the middle of the song, or at its
            very beginning. In that case, the player may have had no
            time to actualize its status to the server
        """
        player_error = PlayerErrorSerializer(data=request.data)

        if player_error.is_valid():
            player = get_player()
            entry_error_id = player_error.validated_data['playlist_entry']
            entry_current = player.playlist_entry
            # protection if the erroneous song is the first one to play
            entry_current_id = entry_current.id if entry_current else 0
            entry_next = get_next_playlist_entry(entry_current_id)
            # protectionif the erroneous song is the last one to play
            entry_next_id = entry_next.id if entry_next else 0

            if entry_error_id == entry_current_id:
                # the server knows the player has already
                # started playing
                entry_to_delete = entry_current
                # change player status
                player.playlist_entry = None
                player.save()
            elif entry_error_id == entry_next_id:
                # the server does not know the player has
                # started playing,
                # which means the error occured immediately and
                # status of the player has not been updated yet
                entry_to_delete = entry_next
            else:
                # TODO error
                message = 'ERROR Player is not supposed to do that'
                logger.error(message)
                raise Exception(message)

            assert entry_to_delete is not None, "Player is playing something inconsistent"

            logger.warning("WARNING Unable to play {song}, \
remove from playlist\n\
Error message: {error_message}".format(
                song=entry_to_delete.song,
                error_message=player_error.validated_data['error_message']
                ))
            # remove the problematic song from the playlist
            entry_to_delete.delete()

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
    if not playlist :
        return None
    playlist_entry = playlist[0]
    return playlist_entry 

def get_player():
    """ Load or create a new player
    """
    with lock:
        return Player.objects.get_or_create()[0]

def get_player_command():
    """ Load or create player command
    """
    return PlayerCommand.objects.get_or_create()[0]




