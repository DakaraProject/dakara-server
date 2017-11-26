from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
        RetrieveUpdateDestroyAPIView,
        ListCreateAPIView,
        )

from . import models
from . import serializers
from . import permissions


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
            permissions.IsPlaylistManagerOrOwnerOrReadOnly
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
            permissions.IsPlaylistUserOrReadOnly
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
            permissions.IsPlaylistManagerOrPlayingEntryOwnerOrReadOnly
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


class PlayerView(APIView):
    """Shorthand for the view of player data
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

        serializer = serializers.PlayerDetailsCommandErrorsSerializer(
                {
                    "status": player,
                    "manage": player_command,
                    "errors": player_errors_pool.dump(),
                },
                context={'request': request},
            )

        return Response(
                serializer.data,
                status.HTTP_200_OK
                )
