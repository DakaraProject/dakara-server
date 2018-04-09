from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
        DestroyAPIView,
        ListCreateAPIView,
        ListAPIView,
        RetrieveUpdateAPIView
        )

from . import models
from . import serializers
from . import permissions

from . import views_device as device


tz = timezone.get_default_timezone()


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
        player = models.Player.get_or_create()
        entry_id = player.playlist_entry_id
        return models.PlaylistEntry.objects.exclude(
                Q(pk=entry_id) | Q(was_played=True)
                ).order_by('date_created')


class PlaylistEntryListView(ListCreateAPIView):
    """List of entries or creation of a new entry in the playlist
    """
    permission_classes = [
            permissions.IsPlaylistUserOrReadOnly,
            permissions.IsPlaylistAndLibraryManagerOrSongCanBeAdded,
            permissions.KaraStatusIsNotStoppedOrReadOnly,
            ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return serializers.PlaylistEntrySerializer

        return serializers.PlaylistEntriesReadSerializer

    def get_queryset(self):
        player = models.Player.get_or_create()
        entry_id = player.playlist_entry_id
        return models.PlaylistEntry.objects.exclude(
                Q(pk=entry_id) | Q(was_played=True)
                ).order_by('date_created')

    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())
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

        serializer = self.get_serializer({
            'results': queryset,
            'date_end': date,
            })

        return Response(serializer.data)


class PlaylistPlayedEntryListView(ListAPIView):
    """List of played entries
    """
    pagination_class = PlaylistEntryPagination
    serializer_class = serializers.PlaylistPlayedEntryReadSerializer
    queryset = models.PlaylistEntry.objects.filter(was_played=True) \
                .order_by('date_created')


class PlayerStatusView(APIView):
    """View of the player status
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Get player status
            Create one if it doesn't exist
        """
        player = models.Player.get_or_create()
        serializer = serializers.PlayerDetailsSerializer(
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

    def get(self, request):
        """Get pause or skip status
        """
        player_command = models.PlayerCommand.get_or_create()
        serializer = serializers.PlayerCommandSerializer(player_command)

        return Response(
                serializer.data,
                status.HTTP_200_OK
                )

    def put(self, request):
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

    def get(self, request):
        """Send player error pool
        """
        player_errors_pool = models.PlayerErrorsPool.get_or_create()
        serializer = serializers.PlayerErrorsPoolSerializer(
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
        - player_status: Player status
        - player_manage: Player manage pause/skip
        - player_errors: Errors from the players
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """Send aggregated player data
        """
        # Get player
        player = models.Player.get_or_create()

        # Get player commands
        player_command = models.PlayerCommand.get_or_create()

        # Get player errors
        player_errors_pool = models.PlayerErrorsPool.get_or_create()

        # Get kara status
        kara_status = models.KaraStatus.get_object()

        serializer = serializers.DigestSerializer(
                {
                    "player_status": player,
                    "player_manage": player_command,
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
    queryset = models.KaraStatus.objects.all()
    serializer_class = serializers.KaraStatusSerializer
    permission_classes = [
            permissions.IsPlaylistManagerOrReadOnly,
            ]

    def put(self, request):
        response = super().put(request)

        # empty the playlist and clear the player if the status is stop
        if response.status_code == status.HTTP_200_OK:
            kara_status = request.data['status']

            if kara_status == models.KaraStatus.STOP:
                player = models.Player.get_or_create()
                player.reset()
                player.save()
                models.PlaylistEntry.objects.all().delete()

        return response

    def get_object(self, *args, **kwargs):
        kara_status, _ = self.queryset.get_or_create(pk=1)
        return kara_status
