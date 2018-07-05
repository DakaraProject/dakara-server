import logging

from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    DestroyAPIView,
    ListCreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from playlist import models
from playlist import serializers
from playlist import permissions

tz = timezone.get_default_timezone()
channel_layer = get_channel_layer()
logger = logging.getLogger(__name__)


class PlaylistEntryPagination(PageNumberPagination):
    """Pagination setup for playlist entries
    """
    page_size = 100


class PlaylistEntryView(DestroyAPIView):
    """Edition of a playlist entry
    """
    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        permissions.IsPlaylistManagerOrOwnerOrReadOnly,
        permissions.KaraStatusIsNotStoppedOrReadOnly,
    ]

    def get_queryset(self):
        return models.PlaylistEntry.get_playlist()


class PlaylistEntryListView(ListCreateAPIView):
    """List of entries or creation of a new entry in the playlist
    """
    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        permissions.IsPlaylistUserOrReadOnly,
        permissions.IsPlaylistAndLibraryManagerOrSongCanBeAdded,
        permissions.KaraStatusIsNotStoppedOrReadOnly,
    ]

    def get_queryset(self):
        return models.PlaylistEntry.get_playlist()

    def get(self, request, *args, **kwargs):
        entries, date = models.PlaylistEntry.get_playlist_with_date()

        serializer = serializers.PlaylistEntriesWithDateEndSerializer(
            {
                'entries': entries,
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

        # was the playlist empty before creation?
        was_empty = models.PlaylistEntry.get_next() is None

        response = super().post(request)

        if response.status_code == status.HTTP_201_CREATED:
            # broadcast that a new entry has been created
            async_to_sync(channel_layer.group_send)('playlist.front', {
                'type': 'send.playlist_new_entry',
            })

            # request the player to play this entry immediately if the playlist
            # was empty and the kara status is set to play
            entry = models.PlaylistEntry.get_next()
            kara_status = models.KaraStatus.get_object()
            if kara_status.status == models.KaraStatus.PLAY and \
               was_empty and entry is not None:
                async_to_sync(channel_layer.group_send)('playlist.device', {
                    'type': 'send.new_entry',
                    'data': {
                        'entry': entry,
                    }
                })

        return response


class PlaylistPlayedEntryListView(ListAPIView):
    """List of played entries
    """
    pagination_class = PlaylistEntryPagination
    serializer_class = serializers.PlaylistPlayedEntryWithDatePlayedSerializer
    queryset = models.PlaylistEntry.objects.filter(was_played=True) \
        .order_by('date_created')


class PlayerStatusView(APIView):
    """View of the player status
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """Get player status

        Create one if it doesn't exist.
        """
        player = models.Player.get_or_create()
        serializer = serializers.PlayerStatusSerializer(
            player,
            context={'request': request}
        )

        return Response(
            serializer.data,
            status.HTTP_200_OK
        )


class PlayerManageView(APIView):
    """View or edition of player commands
    """
    permission_classes = [
        permissions.IsPlaylistManagerOrPlayingEntryOwnerOrReadOnly,
        permissions.KaraStatusIsNotStoppedOrReadOnly,
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


class PlayerErrorsPoolView(APIView):
    """View of the player errors pool
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Send player error pool
        """
        player_errors_pool = models.PlayerErrorsPool.get_or_create()
        serializer = serializers.PlayerErrorSerializer(
            player_errors_pool.dump(),
            many=True,
            context={'request': request}
        )

        return Response(
            serializer.data,
            status.HTTP_200_OK
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
        # Get player errors
        player_errors_pool = models.PlayerErrorsPool.get_or_create()

        # Get kara status
        kara_status = models.KaraStatus.get_object()

        serializer = serializers.DigestSerializer(
            {
                "player_errors": player_errors_pool.dump(),
                "kara_status": kara_status,
            },
            context={'request': request},
        )

        return Response(
            serializer.data,
            status.HTTP_200_OK
        )


class KaraStatusView(RetrieveUpdateAPIView):
    """Get or edit the kara status
    """
    queryset = models.KaraStatus.objects.all()
    serializer_class = serializers.KaraStatusSerializer
    permission_classes = [
        permissions.IsPlaylistManagerOrReadOnly,
    ]

    def put(self, request, *args, **kwargs):
        """Update the kara status
        """
        response = super().put(request)

        if response.status_code == status.HTTP_200_OK:
            kara_status = request.data

            # if the kara has to stop
            if kara_status['status'] == models.KaraStatus.STOP:
                # request the player to stop playing
                async_to_sync(channel_layer.group_send)('playlist.device', {
                    'type': 'send.idle'
                })

                # empty the playlist
                models.PlaylistEntry.objects.all().delete()

                # the empty playlist is not broadcasted, as it can be deduced
                # from the kara status itself

            # if the kara has to be playing
            elif kara_status['status'] == models.KaraStatus.PLAY:
                # request the player to start playing
                async_to_sync(channel_layer.group_send)('playlist.device', {
                    'type': 'handle.new_entry'
                })

            # broadcast the new kara status
            async_to_sync(channel_layer.group_send)('playlist.front', {
                'type': 'send.kara_status',
                'data': {
                    'kara_status': kara_status
                }
            })

        return response

    def get_object(self):
        return models.KaraStatus.get_object()
