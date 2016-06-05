from rest_framework.generics import RetrieveUpdateDestroyAPIView, \
                                    ListCreateAPIView
from django.db.models.functions import Lower
from library.models import Song, Artist, Work
from library.serializers import SongSerializer
from django.db.models import Q


class SongList(ListCreateAPIView):
    """ Class for listing songs
    """
    serializer_class = SongSerializer

    def get_queryset(self):
        """ Filter the songs
        """
        if 'query' in self.request.query_params:
            query = self.request.query_params.get('query', None)
            if query is not None:
                return Song.objects.filter(
                        Q(title__icontains=query) |
                        Q(artists__name__icontains=query) |
                        Q(works__title__icontains=query)
                    ).order_by(Lower('title'))

        return Song.objects.all().order_by(Lower('title'))


class SongDetailView(RetrieveUpdateDestroyAPIView):
    """ Class for displaying song details
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer
