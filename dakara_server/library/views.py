import logging

from django.contrib.auth import get_user_model
from django.db.models.functions import Lower
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from internal import permissions as internal_permissions
from internal.views_mixins import MultiSerializerMixin, QueryParsedListMixin
from library import models, permissions, serializers
from library.query import query_artists, query_songs, query_works

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class SongListView(QueryParsedListMixin, MultiSerializerMixin, ListCreateAPIView):
    """List of songs."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.SongSerializer

    def get_queryset(self):
        """Search and filter the songs."""
        query_set = models.Song.objects.all()

        # hide all songs with disabled tags for non-managers or non-superusers
        user = self.request.user
        if not (user.is_superuser or user.is_library_manager):
            query_set = query_set.exclude(tags__disabled=True)

        return self.perform_query(query_set, query_songs).order_by(Lower("title"))


class SongView(RetrieveUpdateDestroyAPIView):
    """Edition and display of a song."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.Song.objects.all()
    serializer_class = serializers.SongSerializer


class SongRetrieveListView(ListAPIView):
    """List of all songs.

    For the feeder."""

    permission_classes = [IsAuthenticated, permissions.IsLibraryManager]
    queryset = models.Song.objects.all()
    serializer_class = serializers.SongForFeederSerializer
    pagination_class = None


class ArtistListView(QueryParsedListMixin, ListCreateAPIView):
    """List of artists."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.ArtistWithCountSerializer

    def get_queryset(self):
        """Search and filter the artists."""
        query_set = models.Artist.objects.all()

        return self.perform_query(query_set, query_artists).order_by(Lower("name"))


class ArtistPruneView(APIView):
    """Views for artists to delete.

    For the feeder."""

    permission_classes = [IsAuthenticated, permissions.IsLibraryManager]
    queryset = models.Artist.objects.filter(song=None)
    serializer_class = None

    def delete(self, request, *args, **kwargs):
        _, deleted_count = self.queryset.delete()

        return Response(
            {"deleted_count": deleted_count.get("library.Artist", 0)},
            status=status.HTTP_200_OK,
        )


class WorkListView(QueryParsedListMixin, MultiSerializerMixin, ListCreateAPIView):
    """List of works."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    serializer_class = serializers.WorkSerializer

    def get_queryset(self):
        """Search and filter the works."""
        query_set = models.Work.objects.all()

        # if 'type' is in the query string
        # then filter work type
        if "type" in self.request.query_params:
            work_type = self.request.query_params.get("type", None)
            if work_type:
                query_set = query_set.filter(work_type__query_name=work_type)

        return self.perform_query(query_set, query_works).order_by(
            Lower("title"), Lower("subtitle")
        )


class WorkView(RetrieveUpdateDestroyAPIView):
    """Edition and display of a song."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.Work.objects.all()
    serializer_class = serializers.WorkSerializer


class WorkRetrieveListView(ListAPIView):
    """List of all works.

    For the feeder."""

    permission_classes = [IsAuthenticated, permissions.IsLibraryManager]
    queryset = models.Work.objects.all()
    serializer_class = serializers.WorkForFeederSerializer
    pagination_class = None


class WorkPruneView(APIView):
    """Views for works to delete.

    For the feeder."""

    permission_classes = [IsAuthenticated, permissions.IsLibraryManager]
    queryset = models.Work.objects.filter(song=None)
    serializer_class = None

    def delete(self, request, *args, **kwargs):
        _, deleted_count = self.queryset.delete()

        return Response(
            {"deleted_count": deleted_count.get("library.Work", 0)},
            status=status.HTTP_200_OK,
        )


class WorkTypeListView(ListCreateAPIView):
    """List of work types."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.WorkType.objects.all().order_by(Lower("name"))
    serializer_class = serializers.WorkTypeSerializer


class WorkTypeView(RetrieveUpdateDestroyAPIView):
    """View for a work type."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.WorkType.objects.all()
    serializer_class = serializers.WorkTypeSerializer


class SongTagListView(ListCreateAPIView):
    """List of song tags."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.SongTag.objects.all().order_by(Lower("name"))
    serializer_class = serializers.SongTagSerializer


class SongTagView(RetrieveUpdateDestroyAPIView):
    """Update a song tag."""

    permission_classes = [
        IsAuthenticated,
        permissions.IsLibraryManager | internal_permissions.IsReadOnly,
    ]
    queryset = models.SongTag.objects.all()
    serializer_class = serializers.SongTagSerializer
