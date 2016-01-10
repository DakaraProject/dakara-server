from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from playlist.models import *
from playlist.serializers import *
from playlist.communications import *
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

    def create(self, request):
        """ Create new playlist entry

            If the playlist was empty, it starts the player right then
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            playlist_entry = serializer.save()
            logger.debug("Added element to the playlist: " + str(playlist_entry))
            # check if the player is playing
            player = Player.objects.get_or_create()[0]
            if not player.playlist_entry:
                # start playing
                player.playlist_entry = playlist_entry
                player.save()
                logger.debug("Playlist started")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlayerToUserView(APIView):
    """ Class to communicate with the user to player management
    """
    permission_classes = (IsAuthenticated,)

    def get_player(self):
        """ Load or create a new player
        """
        return Player.objects.get_or_create()[0]

    def get(self, request):
        """ Display player

            Create one if it doesn't exist
        """
        player = self.get_player()
        serializer = PlayerSerializer(player)
        return Response(
                serializer.data,
                status.HTTP_200_OK
                )

    def put(self, request):
        """ Manage player
        """
        player = self.get_player()
        serializer = PlayerSerializer(data=request.data)
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



class PlayerToPlayerView(APIView):
    """ Class to communicate with the player for player management

        Recieve status from player
        Send commands to player
    """
    permission_classes = (IsAuthenticated,)

    def get_player(self):
        """ Load or create a new player
        """
        return Player.objects.get_or_create()[0]

    # def get(self, request):
    #     """ Show status only
    #         Debuging purpose
    #     """
    #     player = self.get_player()
    #     status = PlayerStatus(
    #             player.playlist_entry.song.pk \
    #                 if player.playlist_entry else None,
    #             player.timing
    #             )
    #     player_status_serializer = PlayerStatusSerializer(status)
    #     return Response(player_status_serializer.data)

    def put(self, request):
        """ Send commands on recieveing status
        """
        player = self.get_player()
        player_status_serializer = PlayerStatusSerializer(
                data=request.data
                )
        if player_status_serializer.is_valid():
            player_status = PlayerStatus(**player_status_serializer.validated_data)
            player_command = PlayerCommand(False, False)
            try:
                # currently playing something?
                if player_status.song_id:
                    # currently supposed to play something?
                    if player.playlist_entry:
                        current_song = player.playlist_entry.song
                        ##
                        # status
                        #

                        # has changed from the previous to the next track
                        if current_song.id != player_status.song_id:
                            next_song = get_next_song()
                            if next_song != player_status.song_id:
                                 # TODO the player is playing something unrequested
                                message = 'Playing something unrequested'
                                logger.error(message)
                                raise Exception(message)
                            player.song = next_song
                            player.timing = player_status.timing
                            player.skip_requested = None
                            player.save()
                            current_song.delete()
                        # the track is currently playing
                        else:
                            player.timing = player_status.timing
                            player.save()

                        ##
                        # command
                        #
                        skip = False
                        # skip requested
                        if player.skip_requested:
                            if player_status.song_id == player.skip_requested.id:
                                skip = True
                        player_command = PlayerCommand(pause=player.pause_requested, skip=skip)
                    else:
                        # TODO the player is playing while not supposed to
                        message = 'Player is playing while not supposed to'
                        logger.error(message)
                        raise Exception(message)

                player_command_serializer = PlayerCommandSerializer(
                        player_command
                        )
                return Response(
                        player_command_serializer.data,
                        status=status.HTTP_202_ACCEPTED
                        )
            except Exception as e:
                logger.exception('Unexpected error')
                raise
        # if invalid data from the player
        return Response(
                player_status_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )


def get_next_song(id):
    """ Returns the next playlist_entry in playlist
    """
    song = PlaylistEntry.objects.exclude(pk=id).order_by('-date_created')[0]
    return song







