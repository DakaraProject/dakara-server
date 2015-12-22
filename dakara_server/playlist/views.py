from django.http import HttpResponse
from rest_framework import viewsets
from playlist.models import *
from playlist.serializers import *
from playlist.communications import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

class PlaylistEntryViewSet(viewsets.ModelViewSet):
    """ Class for playlist view set
    """


class JSONResponse(HttpResponse):
    """ An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

@csrf_exempt
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
            return JSONResponse(player_command_serializer.data)

        return JSONResponse(player_status_serializer.errors, status=400)

    return HttpResponse(status=405)



def get_next_song(id):
    """ Returns the next playlist_entry in playlist
    """
    song = PlaylistEntry.objects.exclude(pk=id).order_by('-date_created')[0]
    return song







