from rest_framework.generics import RetrieveUpdateDestroyAPIView, \
                                    ListCreateAPIView
from django.db.models.functions import Lower
from library.models import Song
from library.serializers import SongSerializer


class SongList(ListCreateAPIView):
    """ Class for listing songs
    """
    serializer_class = SongSerializer

    def get_queryset(self):
        """ Filter the songs
        """
        if 'title' in self.request.query_params:
            title_query = self.request.query_params.get('title', None)
            if title_query is not None:
                return Song.objects.filter(
                        title__icontains=title_query
                        ).order_by(Lower('title'))

        return Song.objects.all().order_by(Lower('title'))


class SongDetailView(RetrieveUpdateDestroyAPIView):
    """ Class for displaying song details
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer
