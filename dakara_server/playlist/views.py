from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404
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
    """Edition or deletion of a playlist entry
    """
    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        permissions.IsPlaylistManagerOrOwnerForDelete,
        permissions.KaraStatusIsNotStoppedOrReadOnly,
    ]

    def get_queryset(self):
        player = models.Player.get_or_create()
        entry_id = player.playlist_entry_id
        return models.PlaylistEntry.objects.exclude(
            Q(pk=entry_id) | Q(was_played=True)
        )

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
        player = models.Player.get_or_create()
        entry_id = player.playlist_entry_id
        return models.PlaylistEntry.objects.exclude(
            Q(pk=entry_id) | Q(was_played=True)
        )

    def get(self, request, *args, **kwargs):
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
    queryset = models.PlaylistEntry.objects.filter(was_played=True)


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

        # empty the playlist and clear the player if the status is stop
        if response.status_code == status.HTTP_200_OK:
            kara_status = request.data['status']

            if kara_status == models.KaraStatus.STOP:
                player = models.Player.get_or_create()
                player.reset()
                player.save()
                models.PlaylistEntry.objects.all().delete()

        return response

    def get_object(self):
        return models.KaraStatus.get_object()
