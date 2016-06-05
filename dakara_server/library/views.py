from rest_framework.generics import RetrieveUpdateDestroyAPIView, \
                                    ListCreateAPIView
from django.db.models.functions import Lower
from library.models import Song, Artist, Work
from library.serializers import SongSerializer
from django.db.models import Q
from .query_language import parse as parse_query


class SongList(ListCreateAPIView):
    """ Class for listing songs
    """
    serializer_class = SongSerializer

    def get_queryset(self):
        """ Filter the songs
        """
        if 'query' in self.request.query_params:
            query = self.request.query_params.get('query', None)
            if query:
                res = parse_query(query)
                q = []
                for artist in res['artists']:
                    q.append(Q(artists__name__icontains=artist))
                for artist in res['artists_exact']:
                    q.append(Q(artists__name__iexact=artist))
                for work in res['works']:
                    q.append(Q(works__title__icontains=work))
                for work in res['works_exact']:
                    q.append(Q(works__title__iexact=work))
                for title in res['titles']:
                    q.append(Q(title__icontains=title))
                for title in res['titles_exact']:
                    q.append(Q(title__iexact=work))
                for remain in res['remaining']:
                    q.append(
                            Q(title__icontains=remain) |
                            Q(artists__name__icontains=remain) |
                            Q(works__title__icontains=remain)
                        )

                filter_query = q.pop()
                for item in q:
                    filter_query &= item

                return Song.objects.filter(
                        filter_query
                    ).order_by(Lower('title'))

        return Song.objects.all().order_by(Lower('title'))


class SongDetailView(RetrieveUpdateDestroyAPIView):
    """ Class for displaying song details
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer
