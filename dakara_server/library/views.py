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
from library import models, permissions, serializers
from library.query import query_artists, query_songs, query_works

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class QueryParsedListMixin:
    """Mixin that adds parsed query to list response."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.query_parsed = None

    def list(self, request, *args, **kwargs):
        """Add the parsed query to the serialized response."""
        response = super().list(request, *args, **kwargs)

        # pass the query words to highlight to the response
        # the words have been passed to the object in the get_queryset method
        # now, they have to be passed to the response
        # this is why this function in overloaded
        if self.query_parsed is not None:
            response.data["query"] = self.query_parsed

        return response


class MultiSerializerMixin:
    """Mixin that adapts serializer if a list of data is provided."""

    def get_serializer(self, *args, **kwargs):
        """Select accurate serializer to handle list of songs.

        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        data = kwargs.get("data")
        many = kwargs.get("many")

        # check if the serializer is used to deserialize data
        # and check if the data is a list
        if data and isinstance(data, list) and many is None:
            return super().get_serializer(*args, many=True, **kwargs)

        # otherwise
        return super().get_serializer(*args, **kwargs)


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

        # if 'query' is in the query string then perform search otherwise
        # return all songs
        if "query" not in self.request.query_params:
            return query_set.order_by(Lower("title"))

        query = self.request.query_params.get("query", None)
        if query:
            # query the song and save the parsed query
            # to give it back to the client
            query_set, self.query_parsed = query_songs(query_set, query)

        return query_set.distinct().order_by(Lower("title"))


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

        # if 'query' is in the query string then perform search return results
        # of the corresponding query
        if "query" not in self.request.query_params:
            return query_set.order_by(Lower("name"))

        query = self.request.query_params.get("query", None)
        if query:
            query_set, res = query_artists(query_set, query)
            # saving the parsed query to give it back to the client
            self.query_parsed = {"remaining": res}

        return query_set.order_by(Lower("name"))


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

        # if 'query' is in the query string then perform search return results
        # of the corresponding query and type filter
        if "query" not in self.request.query_params:
            return query_set.order_by(Lower("title"), Lower("subtitle"))

        query = self.request.query_params.get("query", None)
        if query:
            query_set, res = query_works(query_set, query)
            # saving the parsed query to give it back to the client
            self.query_parsed = {"remaining": res}

        return query_set.distinct().order_by(Lower("title"), Lower("subtitle"))


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
