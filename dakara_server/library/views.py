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
                q_artist = []
                for artist in res['artists']:
                    q_artist.append(Q(artists__name__icontains=artist))
                for artist in res['artists_exact']:
                    q_artist.append(Q(artists__name__iexact=artist))
                for work in res['works']:
                    q.append(Q(works__title__icontains=work))
                for work in res['works_exact']:
                    q.append(Q(works__title__iexact=work))
                for title in res['titles']:
                    q.append(Q(title__icontains=title))
                for title in res['titles_exact']:
                    q.append(Q(title__iexact=title))
                for remain in res['remaining']:
                    q.append(
                            Q(title__icontains=remain) |
                            Q(artists__name__icontains=remain) |
                            Q(works__title__icontains=remain)
                        )

                filter_query = Q() 
                for item in q:
                    filter_query &= item

                query_set = Song.objects.filter(filter_query)
                
                for item in q_artist:
                    query_set = query_set.filter(item)

                # saving the query to give it back to the client
                self.query_parsed = res

                return query_set.distinct().order_by(Lower('title'))

        return Song.objects.all().order_by(Lower('title'))

    def list(self, request, *args, **kwargs):
        """ Send a listing of songs
        """
        response = super(SongList, self).list(request, args, kwargs)

        # pass the query words to highlight to the response
        if hasattr(self, 'query_parsed'):
            response.data['query'] = self.query_parsed

        return response


class SongDetailView(RetrieveUpdateDestroyAPIView):
    """ Class for displaying song details
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer
