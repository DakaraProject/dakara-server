import logging
from datetime import datetime, timedelta

from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics as drf_generics

from internal import permissions as internal_permissions
from internal.pagination import PageNumberPaginationCustom
from library import permissions as library_permissions
from playlist import models
from playlist import serializers
from playlist import permissions
from playlist.consumers import send_to_channel
from playlist.date_stop import KARAOKE_JOB_NAME, scheduler, clear_date_stop

tz = timezone.get_default_timezone()
logger = logging.getLogger(__name__)
UserModel = get_user_model()


class PlaylistEntryPagination(PageNumberPaginationCustom):
    """Pagination setup for playlist entries
    """

    page_size = 100


class PlaylistEntryView(drf_generics.DestroyAPIView):
    """Edition or deletion of a playlist entry
    """

    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        IsAuthenticated,
        permissions.IsPlaylistManager
        | (internal_permissions.IsDelete & permissions.IsOwner),
    ]
    queryset = models.PlaylistEntry.get_playlist()

    def put(self, request, *args, **kwargs):
        playlist_entry = self.get_object()

        serializer = serializers.PlaylistReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        if "before_id" in serializer.data:
            before_id = serializer.data["before_id"]
            before_entry = get_object_or_404(self.get_queryset(), pk=before_id)
            playlist_entry.above(before_entry)

        else:
            after_id = serializer.data["after_id"]
            after_entry = get_object_or_404(self.get_queryset(), pk=after_id)
            playlist_entry.below(after_entry)

        return Response(status=status.HTTP_204_NO_CONTENT)


class PlaylistEntryListView(drf_generics.ListCreateAPIView):
    """List of entries or creation of a new entry in the playlist
    """

    serializer_class = serializers.PlaylistEntrySerializer
    permission_classes = [
        IsAuthenticated,
        permissions.IsPlaylistUser | internal_permissions.IsReadOnly,
        (permissions.IsPlaylistManager & library_permissions.IsLibraryManager)
        | permissions.IsSongEnabled,
    ]
    queryset = models.PlaylistEntry.get_playlist()

    def get(self, request, *args, **kwargs):
        queryset = self.queryset.all()
        player = models.Player.get_or_create()
        date = datetime.now(tz)

        # add player remaining time
        if player.playlist_entry:
            date += player.playlist_entry.song.duration - player.timing

        # for each entry, compute when it is supposed to play
        for playlist_entry in queryset:
            playlist_entry.date_play = date
            date += playlist_entry.song.duration

        serializer = serializers.PlaylistEntriesWithDateEndSerializer(
            {"results": queryset, "date_end": date}, context={"request": request}
        )

        return Response(serializer.data)

    def perform_create(self, serializer):
        # Deny creation if kara is not ongoing
        karaoke = models.Karaoke.get_object()
        if not karaoke.ongoing:
            raise PermissionDenied(detail="Karaoke is not ongoing.")

        # Deny creation if karaoke does not allow new entries,
        # and user is not manager.
        if (
            not karaoke.can_add_to_playlist
            and not self.request.user.is_playlist_manager
            and not self.request.user.is_superuser
        ):
            raise PermissionDenied(
                detail="Karaoke was set to disallow playlist entries creation."
            )

        # Deny the creation of a new playlist entry if it exceeds the playlist
        # capacity set in settings.
        queryset = self.filter_queryset(self.get_queryset())
        count = queryset.count()

        if count >= settings.PLAYLIST_SIZE_LIMIT:
            raise PermissionDenied(detail="Playlist is full, please retry later.")

        # Deny the creation of a new playlist entry if it exceeds karaoke stop
        # date. This case cannot be handled through permission classes at view
        # level, as permission examination takes place before the data are
        # validated. Moreover, the object permission method won't be called as
        # we are creating the object (which obviously doesn't exist yet).

        if karaoke.date_stop is not None and not (
            self.request.user.is_playlist_manager or self.request.user.is_superuser
        ):
            # compute playlist end date
            playlist = self.filter_queryset(self.get_queryset())
            player = models.Player.get_or_create()
            date = datetime.now(tz)

            # add player remaining time
            if player.playlist_entry:
                date += player.playlist_entry.song.duration - player.timing

            # compute end time of playlist
            for playlist_entry in playlist:
                date += playlist_entry.song.duration

            # add current entry duration
            date += serializer.validated_data["song"].duration

            # check that this date does not exceed the stop date
            if date > karaoke.date_stop:
                raise PermissionDenied("This song exceeds the karaoke stop time")

        playlist_was_empty = models.PlaylistEntry.get_next() is None

        # add the owner to the serializer and create data
        serializer.save(owner=self.request.user)

        # TODO broadcast that a new entry has been created

        # Request the player to play the latest playlist entry immediately if :
        #   - it exists;
        #   - the playlist was empty beforehand;
        #   - player is set to play next song
        #   - the player is idle.
        next_playlist_entry = models.PlaylistEntry.get_next()
        player = models.Player.get_or_create()
        if all(
            (
                next_playlist_entry is not None,
                playlist_was_empty,
                karaoke.player_play_next_song,
                player.playlist_entry is None,
            )
        ):
            send_to_channel(
                "playlist.device",
                "send_playlist_entry",
                {"playlist_entry": next_playlist_entry},
            )


class PlaylistPlayedEntryListView(drf_generics.ListAPIView):
    """List of played entries
    """

    pagination_class = PlaylistEntryPagination
    serializer_class = serializers.PlaylistPlayedEntryWithDatePlayedSerializer
    queryset = models.PlaylistEntry.get_playlist_played()


class PlayerCommandView(drf_generics.UpdateAPIView):
    """Handle player commands
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsPlaylistManager
        | permissions.IsPlayingEntryOwner
        | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.PlayerCommandSerializer

    def perform_update(self, serializer):
        # check the karaoke is ongoing
        karaoke = models.Karaoke.get_object()
        if not karaoke.ongoing:
            raise PermissionDenied(
                "The player cannot receive commands if the karaoke is not ongoing"
            )

        # check the player is not idle
        player = models.Player.get_or_create()
        if player.playlist_entry is None:
            raise PermissionDenied("The player cannot receive commands when " "idle")

        command = serializer.validated_data["command"]
        send_to_channel("playlist.device", "send_command", {"command": command})

    def get_object(self):
        return None


class DigestView(APIView):
    """Shorthand for the view of playlist data

    Includes:
        - player_status: current player;
        - player_errors: errors from the player;
        - karaoke: current karaoke session.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Send aggregated player data
        """
        # Get player
        player = models.Player.get_or_create()

        # manually update the player timing
        now = datetime.now(tz)
        if player.playlist_entry:
            if not player.paused:
                player.update(timing=player.timing + (now - player.date), date=now)

        # Get player errors
        player_errors_pool = models.PlayerError.objects.all()

        # Get kara status
        karaoke = models.Karaoke.get_object()

        serializer = serializers.DigestSerializer(
            {
                "player_status": player,
                "player_errors": player_errors_pool,
                "karaoke": karaoke,
            }
        )

        return Response(serializer.data, status.HTTP_200_OK)


class KaraokeView(drf_generics.RetrieveUpdateAPIView):
    """Get or edit the kara status
    """

    queryset = models.Karaoke.objects.all()
    serializer_class = serializers.KaraokeSerializer
    permission_classes = [
        IsAuthenticated,
        permissions.IsPlaylistManager | internal_permissions.IsReadOnly,
    ]

    def perform_update(self, serializer):
        """Update the karaoke
        """
        super().perform_update(serializer)
        karaoke = serializer.instance

        # Management of date stop

        if "date_stop" in serializer.validated_data:
            # Clear existing scheduled task
            existing_job_id = cache.get(KARAOKE_JOB_NAME)
            if existing_job_id is not None:
                existing_job = scheduler.get_job(existing_job_id)
                if existing_job is not None:
                    existing_job.remove()
                    logger.debug("Existing date stop job was found and unscheduled")

                else:
                    cache.delete(KARAOKE_JOB_NAME)

            if karaoke.date_stop is not None:
                # Schedule date stop clear
                job = scheduler.add_job(
                    clear_date_stop, "date", run_date=karaoke.date_stop
                )
                cache.set(KARAOKE_JOB_NAME, job.id)
                logger.debug("New date stop job was scheduled")

        # Management of kara status Booleans change

        # empty the playlist and clear the player if the kara is switched to not ongoing
        if "ongoing" in serializer.validated_data and not karaoke.ongoing:
            # request the player to be idle
            send_to_channel("playlist.device", "send_idle")

            # clear player
            player = models.Player()
            player.save()

            # empty the playlist
            models.PlaylistEntry.objects.all().delete()

            # empty the player errors
            models.PlayerError.objects.all().delete()

            return

        if (
            karaoke.ongoing
            and "player_play_next_song" in serializer.validated_data
            and karaoke.player_play_next_song
        ):
            player = models.Player.get_or_create()

            # request the player to play the next song if idle,
            # and there is a next song to play
            if player.playlist_entry is None:
                next_playlist_entry = models.PlaylistEntry.get_next()
                if next_playlist_entry is not None:
                    send_to_channel(
                        "playlist.device",
                        "send_playlist_entry",
                        data={"playlist_entry": next_playlist_entry},
                    )

    def get_object(self):
        return models.Karaoke.get_object()


class PlayerStatusView(drf_generics.RetrieveUpdateAPIView):
    """View of the player

    It allows to get and set the player status.
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsPlayer | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.PlayerStatusSerializer

    def perform_update(self, serializer):
        """Handle the new status
        """
        player = serializer.instance
        entry = serializer.validated_data["playlist_entry"]
        event = serializer.validated_data["event"]

        # get the method associated to the event
        method_name = "receive_{}".format(event)
        if not hasattr(self, method_name):
            # in this case, we raise an error to inform the client that its
            # request is invalid
            raise ValueError("This event is not valid '{}'".format(event))

        method = getattr(self, method_name)

        # call the method
        player.update(**serializer.validated_data)
        method(entry, player)
        player.save()

        # broadcast to the front
        # send_to_channel("playlist.front", "send.player.status", {"player": player})

    def receive_finished(self, playlist_entry, player):
        """The player finished a song
        """
        # set the playlist entry as finished
        playlist_entry.set_finished()

        # reset the player
        player.reset()

        # log the info
        logger.debug("The player has finished playing '%s'", playlist_entry)

        # continue the playlist
        send_to_channel("playlist.device", "handle_next")

    def receive_could_not_play(self, playlist_entry, player):
        """The player could not play a song
        """
        # set the playlist entry as started and already finished
        playlist_entry.set_playing()
        playlist_entry.set_finished()

        # log the info
        logger.debug("The player could not play '%s'", playlist_entry)

        # continue the playlist
        send_to_channel("playlist.device", "handle_next")

    def receive_started_transition(self, playlist_entry, player):
        """The player started the transition of a playlist entry
        """
        # set the playlist entry as started
        playlist_entry.set_playing()

        # update the player
        player.update(in_transition=True, timing=timedelta(seconds=0))

        # log the info
        logger.debug("Playing transition of entry '%s'", playlist_entry)

    def receive_started_song(self, playlist_entry, player):
        """The player started the song of a playlist entry
        """
        # update the player
        player.update(in_transition=False)

        # log the info
        logger.debug("Playing song of entry '%s'", playlist_entry)

    def receive_paused(self, playlist_entry, player):
        """The player switched to pause
        """
        # update the player
        player.update(paused=True)

        # log the info
        logger.debug("The player switched to pause")

    def receive_resumed(self, playlist_entry, player):
        """The player resumed playing
        """
        # update the player
        player.update(paused=False)

        # log the info
        logger.debug("The player resumed playing")

    def get_object(self):
        return models.Player.get_or_create()


class PlayerErrorView(drf_generics.ListCreateAPIView):
    """View of the player errors
    """

    permission_classes = [
        IsAuthenticated,
        permissions.IsPlayer | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.PlayerErrorSerializer
    queryset = models.PlayerError.objects.order_by("date_created")

    def perform_create(self, serializer):
        """Create an error and perform other actions

        Log the error and broadcast it to the front. Then, continue the
        playlist.
        """
        super().perform_create(serializer)
        playlist_entry = serializer.validated_data["playlist_entry"]
        message = serializer.validated_data["error_message"]

        # log the event
        logger.warning(
            "Unable to play '%s', remove from playlist, error message: %s",
            playlist_entry,
            message,
        )

        # broadcast the error to the front
        # send_to_channel(
        #     "playlist.front",
        #     "send.player.error",
        #     {"player_error": serializer.instance},
        # )
