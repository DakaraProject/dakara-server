import logging
from datetime import datetime

from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics as drf_generics

from playlist import models
from playlist import serializers
from playlist import permissions
from playlist.consumers import broadcast_to_channel

tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)
UserModel = get_user_model()


class PlaylistEntryPagination(PageNumberPagination):
    """Pagination setup for playlist entries
    """
    page_size = 100


class PlaylistEntryView(drf_generics.DestroyAPIView):
    """Edition or deletion of a playlist entry
    """
    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        permissions.IsPlaylistManagerOrOwnerForDelete,
    ]
    queryset = models.PlaylistEntry.get_playlist()

    def put(self, request, *args, **kwargs):
        playlist_entry = self.get_object()

        serializer = serializers.PlaylistReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        if 'before_id' in serializer.data:
            before_id = serializer.data['before_id']
            before_entry = get_object_or_404(self.get_queryset(), pk=before_id)
            playlist_entry.above(before_entry)

        else:
            after_id = serializer.data['after_id']
            after_entry = get_object_or_404(self.get_queryset(), pk=after_id)
            playlist_entry.below(after_entry)

        return Response(status=status.HTTP_204_NO_CONTENT)


class PlaylistEntryListView(drf_generics.ListCreateAPIView):
    """List of entries or creation of a new entry in the playlist
    """
    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        permissions.IsPlaylistUserOrReadOnly,
        permissions.IsPlaylistAndLibraryManagerOrSongCanBeAdded,
        permissions.KaraokeIsNotStoppedOrReadOnly,
    ]
    queryset = models.PlaylistEntry.get_playlist()

    def get(self, request, *args, **kwargs):
        queryset = self.queryset.all()
        player = models.Player.get_or_create()
        date = datetime.now(tz)

        # add player remaining time
        if player.playlist_entry_id:
            playlist_entry = models.PlaylistEntry.objects.get(
                pk=player.playlist_entry_id
            )
            date += playlist_entry.song.duration - player.timing

        # for each entry, compute when it is supposed to play
        for playlist_entry in queryset:
            playlist_entry.date_play = date
            date += playlist_entry.song.duration

        serializer = serializers.PlaylistEntriesWithDateEndSerializer(
            {
                'results': queryset,
                'date_end': date,
            },
            context={'request': request}
        )

        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        count = queryset.count()

        # deny the creation of a new playlist entry if the playlist is full
        if count >= settings.PLAYLIST_SIZE_LIMIT:
            raise PermissionDenied(
                detail="Playlist is full, please retry later."
            )

        return super().post(request)

    def perform_create(self, serializer):
        # Deny the creation of a new playlist entry if it exeeds karaoke stop
        # date. This case cannot be handled through permission classes at view
        # level, as permission examination takes place before the data are
        # validated. Moreover, the object permission method won't be called as
        # we are creating the object (which obviously doesn't exist yet).
        karaoke = models.Karaoke.get_object()

        if karaoke.date_stop is not None and \
           not self.request.user.has_playlist_permission_level(
               UserModel.MANAGER) and \
           not self.request.user.is_superuser:
            # compute playlist end date
            playlist = self.filter_queryset(self.get_queryset())
            player = models.Player.get_or_create()
            date = datetime.now(tz)

            # add player remaining time
            if player.playlist_entry_id:
                playlist_entry = models.PlaylistEntry.objects.get(
                    pk=player.playlist_entry_id
                )
                date += playlist_entry.song.duration - player.timing

            # compute end time of playlist
            for playlist_entry in playlist:
                date += playlist_entry.song.duration

            # add current entry duration
            date += serializer.validated_data['song'].duration

            # check that this date does not exceed the stop date
            if date > karaoke.date_stop:
                raise PermissionDenied(
                    "This song exceeds the karaoke stop time")

        super().perform_create(serializer)


class PlaylistPlayedEntryListView(drf_generics.ListAPIView):
    """List of played entries
    """
    pagination_class = PlaylistEntryPagination
    serializer_class = serializers.PlaylistPlayedEntryWithDatePlayedSerializer
    queryset = models.PlaylistEntry.get_playlist_played()


class PlayerManageView(APIView):
    """View or edition of player commands
    """
    permission_classes = [
        permissions.IsPlaylistManagerOrPlayingEntryOwnerOrReadOnly,
        permissions.KaraokeIsNotStoppedOrReadOnly,
    ]

    def get(self, request, *args, **kwargs):
        """Get pause or skip status
        """
        player_command = models.PlayerCommand.get_or_create()
        serializer = serializers.PlayerCommandSerializer(player_command)

        return Response(
            serializer.data,
            status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        """Send pause or skip requests
        """
        serializer = serializers.PlayerCommandSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status.HTTP_400_BAD_REQUEST
            )

        player_command = models.PlayerCommand(**serializer.data)
        player_command.save()

        return Response(
            serializer.data,
            status.HTTP_202_ACCEPTED
        )


class DigestView(APIView):
    """Shorthand for the view of digest data

    Includes:
        - player_status: Player status;
        - player_manage: Player manage pause/skip;
        - player_errors: Errors from the players.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Send aggregated player data
        """
        # Get player
        player = models.Player.get_or_create()

        # Get player commands
        player_command = models.PlayerCommand.get_or_create()

        # Get player errors
        player_errors_pool = models.PlayerError.objects.all()

        # Get kara status
        karaoke = models.Karaoke.get_object()

        serializer = serializers.DigestSerializer(
            {
                "player_status": player,
                "player_manage": player_command,
                "player_errors": player_errors_pool,
                "karaoke": karaoke,
            },
            context={'request': request},
        )

        return Response(
            serializer.data,
            status.HTTP_200_OK
        )


class KaraokeView(drf_generics.RetrieveUpdateAPIView):
    """Get or edit the kara status
    """
    queryset = models.Karaoke.objects.all()
    serializer_class = serializers.KaraokeSerializer
    permission_classes = [
        permissions.IsPlaylistManagerOrReadOnly,
    ]

    def perform_update(self, serializer):
        """Update the karaoke
        """
        super().perform_update(serializer)

        # if the status of the karaoke has changed
        if 'status' not in serializer.validated_data:
            return

        # empty the playlist and clear the player if the new status is stop
        karaoke = serializer.instance

        if karaoke.status == models.Karaoke.STOP:
            # request the player to be idle
            broadcast_to_channel('playlist.device', 'send_idle')

            # clear player
            player = models.Player()
            player.save()

            # empty the playlist
            models.PlaylistEntry.objects.all().delete()

            # empty the player errors
            models.PlayerError.objects.all().delete()

        elif karaoke.status == models.Karaoke.PLAY:
            player = models.Player.get_or_create()

            # request the player to play the next song if idle
            if player.playlist_entry is None:
                broadcast_to_channel(
                    'playlist.device', 'send_playlist_entry', data={
                         'playlist_entry': models.PlaylistEntry.get_next()
                     }
                )

    def get_object(self):
        return models.Karaoke.get_object()


class PlayerStatusView(drf_generics.RetrieveUpdateAPIView):
    """View of the player

    It allows to get and set the player status.

    It is important to note that a full update of the player status (PUT) is
    rarely used, since the server pilots the player directly (and sets the
    in-memory `player` object accordingly). This method is only called if
    someone wants to have the current status right now. While it can correct
    some differences with the in-memory player object, it has to be used as
    confirmation. The playlist entry provided must remain the same as the one
    currently playing.

    The partial update of the player status (PATCH) is used for events that
    cannot be predicted by the server (like song finished or not in transition
    anymore).
    """
    permission_classes = [permissions.IsPlayerOrReadOnly]
    serializer_class = serializers.PlayerStatusSerializer

    def perform_update(self, serializer):
        """Handle the new status
        """
        player = self.get_object()
        entry = serializer.validated_data['playlist_entry']

        # the player is idle
        if entry is None:
            # save the player
            player.reset()
            player.save()

            # reset the player instance in the serializer as the player has
            # changed
            serializer.instance = player

            # log the info
            logger.debug("The player is idle")

            # broadcast to the front
            broadcast_to_channel('playlist.front', 'send_player_status',
                                 {'player': player})

            return

        # the player has finished a song
        if serializer.validated_data.get('finished', False):
            # set the playlist entry as finished
            player = entry.set_finished()

            # reset the player instance in the serializer as the player is a
            # different object
            serializer.instance = player

            # log the info
            logger.debug("The player has finished playing '{}'".format(entry))

            # continue the playlist
            # the current state of the player will be broadcasted to the front
            # later
            broadcast_to_channel('playlist.device', 'handle_next')

            return

        # other cases

        # the player is in transition
        if serializer.validated_data.get('in_transition', False):
            # if the player is in transition, it should not have any timing
            serializer.validated_data.pop('timing')

        # general case
        player.update(**serializer.validated_data)
        player.save()

        # reset the player instance in the serializer as the player has changed
        serializer.instance = player

        # log the current state of the player
        logger.debug("The player is {}".format(player))

        # broadcast to the front
        broadcast_to_channel('playlist.front', 'send_player_status',
                             {'player': player})

    def get_object(self):
        return models.Player.get_or_create()


class PlayerErrorView(drf_generics.ListCreateAPIView):
    """View of the player errors
    """
    permission_classes = [permissions.IsPlayerOrReadOnly]
    serializer_class = serializers.PlayerErrorSerializer
    queryset = models.PlayerError.objects.order_by('date_created')
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        """Create an error and perform other actions

        Log the error and broadcast it to the front. Then, continue the
        playlist.
        """
        super().perform_create(serializer)
        playlist_entry = serializer.validated_data['playlist_entry']
        message = serializer.validated_data['error_message']

        # mark the playlist_entry as played
        playlist_entry.set_finished()

        # log the event
        logger.warning(
            "Unable to play '{}', remove from playlist, error message: '{}'"
            .format(playlist_entry, message)
        )

        # broadcast the error to the front
        broadcast_to_channel('playlist.front', 'send_player_error',
                             {'player_error': serializer.instance})

        # continue the playlist
        broadcast_to_channel('playlist.device', 'handle_next')
