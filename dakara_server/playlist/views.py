from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from playlist.models import *
from playlist.serializers import *
from playlist.communications import *

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
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            playlist_entry = serializer.save()
            # check if the player is playing
            player = Player.objects.get_or_create()[0]
            if not player.playlist_entry:
                # start playing
                player.playlist_entry = playlist_entry
                player.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlayerView(APIView):
    """ Class to communicate with the player

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
        print('player', player)
        if player_status_serializer.is_valid():
            print('data validated')
            player_status = PlayerStatus(**player_status_serializer.validated_data)
            player_command = PlayerCommand(False, False)
            print('status', player_status.song_id, player_status.timing)
            try:
                # currently playing something?
                if player_status.song_id:
                    # currently supposed to play something?
                    print('status song id', player_status.song_id)
                    if player.playlist_entry:
                        print('player song id', player.playlist_entry.song.id)
                        current_song = player.playlist_entry.song
                        ##
                        # status
                        #

                        # has changed from the previous to the next track
                        if current_song.id != player_status.song_id:
                            next_song = get_next_song()
                            if next_song != player_status.song_id:
                                 # TODO the player is playing something unrequested
                                message = 'playing sth unrequested'
                                print(message)
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
                        message = 'player is playing while not supposed to'
                        print(message)
                        raise Exception(message)

                player_command_serializer = PlayerCommandSerializer(
                        player_command
                        )
                return Response(
                        player_command_serializer.data,
                        status=status.HTTP_201_CREATED
                        )
            except Exception as e:
                print(e)
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







