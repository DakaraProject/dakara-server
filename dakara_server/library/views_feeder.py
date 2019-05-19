from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from copy import deepcopy

from library import models
from library import serializers
from library import permissions


class FeederListView(ListAPIView):

    permission_classes = [IsAuthenticated, permissions.IsLibraryManager]
    queryset = models.Song.objects.all()
    serializer_class = serializers.SongOnlyFilePathSerializer
    pagination_class = None


class FeederView(CreateAPIView):
    permission_classes = [IsAuthenticated, permissions.IsLibraryManager]
    serializer_class = serializers.FeederSerializer

    def perform_create(self, serializer):
        # get the list serializer for added elements
        # TODO do it in a cleaner way
        data_list = []
        for data in deepcopy(serializer.validated_data["added"]):
            data["works"] = data.pop("songworklink_set")
            data_list.append(data)

        serializer_added = serializers.SongSerializer(data=data_list, many=True)
        serializer_added.is_valid()

        # save the added elements
        serializer_added.save()

        # get the list of deleted elements
        list_deleted = serializer.validated_data["deleted"]

        # remove the deleted elements
        for song in list_deleted:
            models.Song.objects.get(**song).delete()

    #
    # def post(self, request, *args, **kwargs):
    #     serializer = self.serializer_class(request.data)
    #     if not serializer.is_valid():
    #
