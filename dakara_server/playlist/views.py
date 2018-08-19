from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
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
UserModel = get_user_model()


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
        permissions.KaraokeIsNotStoppedOrReadOnly,
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
        karaoke = models.Karaoke.get_object()

        serializer = serializers.DigestSerializer(
            {
                "player_status": player,
                "player_manage": player_command,
                "player_errors": player_errors_pool.dump(),
                "karaoke": karaoke,
            },
            context={'request': request},
        )

        return Response(
            serializer.data,
            status.HTTP_200_OK
        )


class KaraokeView(RetrieveUpdateAPIView):
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
            player = models.Player.get_or_create()
            player.reset()
            player.save()
            models.PlaylistEntry.objects.all().delete()

    def get_object(self):
        return models.Karaoke.get_object()
