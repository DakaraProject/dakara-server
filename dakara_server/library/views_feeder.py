from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from library import models
from library import serializers


class FeederListView(ListAPIView):

    permission_classes = [IsAuthenticated]
    queryset = models.Song.objects.all()
    serializer_class = serializers.SongForFeederSerializer
    pagination_class = None
