from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from playlist.models import *
from playlist.serializers import *
import logging

# logger object
logger = logging.getLogger(__name__)

class PlaylistEntryDetail(RetrieveUpdateDestroyAPIView):
    """ Class for editing an playlist entry
    """
    queryset = PlaylistEntry.objects.all()
    serializer_class = PlaylistEntrySerializer

class PlaylistEntryList(ListCreateAPIView):
    """ Class for listing or creating new entry in the playlist
    """
    queryset = PlaylistEntry.objects.all()
    serializer_class = PlaylistEntrySerializer


class PlayerCommandForUserView(APIView):
    """ Class for the user to view or send commands 
    """
    permission_classes = (IsAuthenticated,)

    def get_player_command(self):
        """ Load or create player command
        """
        return PlayerCommand.objects.get_or_create()[0]

    def get(self, request):
        """ Get playerCommand
            Create one if it doesn't exist
        """
        player_command = self.get_player_command()
        serializer = PlayerCommandSerializer(player_command)
        return Response(
                serializer.data,
                status.HTTP_200_OK
                )

    def put(self, request):
        """ Send pause or skip requests
        """
        player_command = self.get_player_command()
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

    def get_player(self):
        """ Load or create player status 
        """
        return Player.objects.get_or_create()[0]

    def get(self, request):
        """ Get player status
            Create one if it doesn't exist
        """
        player = self.get_player()
        serializer = PlayerSerializer(player)
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

    def get_player(self):
        """ Load or create a new player
        """
        return Player.objects.get_or_create()[0]

    def get_player_command(self):
        """ Load or create player command
        """
        return PlayerCommand.objects.get_or_create()[0]

    def get(self, request):
        """ Get next playist entry 
        """
        player = self.get_player()
        entry = get_next_playlist_entry(player.playlist_entry_id)
        serializer = PlaylistEntryReadSerializer(entry)
        return Response(
                serializer.data,
                status.HTTP_200_OK
                )

    def put(self, request):
        """ Send commands on recieveing status
        """
        
        player_command = self.get_player_command()
        player_old = self.get_player()
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
                            player_command.skip = false
                            player_command.save()

                        #remove previous entry from playlist if there was any
                        if entry_old:
                            entry_old.delete()

                        if player.playlist_entry:
                            logger.info("INFO The player has switched and is at {0} of {1}".format(player.timing, player.playlist_entry.song))
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


def get_next_playlist_entry(id):
    """ Returns the next playlist_entry in playlist
        excluding entry with specified id
    """
    playlist = PlaylistEntry.objects.exclude(pk=id).order_by('date_created')
    if not playlist :
        return None
    playlist_entry = playlist[0]
    return playlist_entry 







