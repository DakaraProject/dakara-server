from rest_framework import viewsets
from playlist.models import *
from playlist.serializers import *
from playlist.communications import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

class PlaylistEntryViewSet(viewsets.ModelViewSet):
    """ Class for playlist view set
    """
    queryset = PlaylistEntry.objects.all()
    serializer_clss = PlaylistEntrySerializer


@api_view(['PUT'])
def player_status(request):
    """ Recieve status from player
        Send commands to player
    """
    if request.method == 'PUT':
        player = Player.object.get_or_create()
        data = JSONParser().parse(request)
        player_status_serializer = PlayerStatusSerializer(data=data)
        if player_status_serializer.is_valid():
            status = PlayerStatus(**player_status_serializer.validated_data)
            command = PlayerCommand(False, False)
            # currently playing something
            if status.song_id:
                ##
                # status
                #

                # has changed from the previous to the next track
                current_song = player.song
                if current_song.id != status.song_id:
                    next_song = get_next_song()
                    if next_song != status.song_id:
                        pass # TODO the player is playing something unrequested
                    player.song = next_song
                    player.timing = status.timing
                    player.skip_requested = None
                    player.save()
                    current_song.delete()
                # the track is currently playing
                else:
                    player.timing = status.timing
                    player.save()

                ##
                # command
                #
                skip = False
                # skip requested
                if player.skip_requested:
                    if status.song_id == player.skip_requested.id:
                        skip = True
                command = Command(pause=player.is_pause_requested, skip=skip)

            player_command_serializer = PlayerCommandSerializer(command)
            return Response(
                    player_command_serializer.data,
                    status=status.HTTP_201_CREATED
                    )

        return Response(
                player_status_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
                )


def get_next_song(id):
    """ Returns the next playlist_entry in playlist
    """
    song = PlaylistEntry.objects.exclude(pk=id).order_by('-date_created')[0]
    return song







