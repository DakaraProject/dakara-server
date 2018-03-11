from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
        RetrieveUpdateDestroyAPIView,
        ListCreateAPIView,
        RetrieveUpdateAPIView
        )

from . import models
from . import serializers
from . import permissions

from . import views_device as device


class PlaylistEntryPagination(PageNumberPagination):
    """Pagination setup for playlist entries
    """
    page_size = 100


class PlaylistEntryView(RetrieveUpdateDestroyAPIView):
    """Edition of a playlist entry
    """
    queryset = models.PlaylistEntry.objects.all()
    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
            permissions.IsPlaylistManagerOrOwnerOrReadOnly,
            permissions.KaraStatusIsNotStoppedOrReadOnly,
            ]

    def destroy(self, request, *args, **kwargs):
        playing_id = models.Player.get_or_create().playlist_entry_id
        instance = self.get_object()
        if playing_id == instance.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlaylistEntryListView(ListCreateAPIView):
    """List of entries or creation of a new entry in the playlist
    """
    pagination_class = PlaylistEntryPagination
    permission_classes = [
            permissions.IsPlaylistUserOrReadOnly,
            permissions.IsPlaylistAndLibraryManagerOrSongCanBeAdded,
            permissions.KaraStatusIsNotStoppedOrReadOnly,
            ]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return serializers.PlaylistEntrySerializer

        return serializers.PlaylistEntryReadSerializer

    def get_queryset(self):
        player = models.Player.get_or_create()
        entry_id = player.playlist_entry_id
        return models.PlaylistEntry.objects.exclude(pk=entry_id) \
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

        serializer = serializers.DigestSerializer(
                {
                    "player_status": player,
                    "player_manage": player_command,
                    "player_errors": player_errors_pool.dump(),
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
