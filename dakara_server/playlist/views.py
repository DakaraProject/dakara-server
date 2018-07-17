from datetime import datetime

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

from playlist import models
from playlist import serializers
from playlist import permissions
from playlist import views_device as device # noqa F401

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
    queryset = models.PlaylistEntry.get_playlist()


class PlaylistEntryListView(ListCreateAPIView):
    """List of entries or creation of a new entry in the playlist
    """
    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        permissions.IsPlaylistUserOrReadOnly,
        permissions.IsPlaylistAndLibraryManagerOrSongCanBeAdded,
        permissions.KaraStatusIsNotStoppedOrReadOnly,
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


class PlaylistPlayedEntryListView(ListAPIView):
    """List of played entries
    """
    pagination_class = PlaylistEntryPagination
    serializer_class = serializers.PlaylistPlayedEntryWithDatePlayedSerializer
    queryset = models.PlaylistEntry.get_playlist_played()


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


class PlayerErrorView(ListAPIView):
    """View of the player errors
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.PlayerErrorSerializer
    queryset = models.PlayerError.objects.all().order_by('date_created')


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
        kara_status = models.KaraStatus.get_object()

        serializer = serializers.DigestSerializer(
            {
                "player_status": player,
                "player_manage": player_command,
                "player_errors": player_errors_pool,
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

        # empty the playlist, the player errors and clear the player if the
        # status is stop
        if response.status_code == status.HTTP_200_OK:
            kara_status = request.data['status']

            if kara_status == models.KaraStatus.STOP:
                # clear player
                player = models.Player.get_or_create()
                player.reset()
                player.save()

                # empty the playlist
                models.PlaylistEntry.objects.all().delete()

                # empty the player errors
                models.PlayerError.objects.all().delete()

        return response

    def get_object(self):
        return models.KaraStatus.get_object()
