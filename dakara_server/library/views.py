from rest_framework.generics import RetrieveUpdateDestroyAPIView, \
                                    ListCreateAPIView
from django.db.models.functions import Lower
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from library.models import Song, Artist, Work
from library.serializers import SongSerializer, \
                                ArtistSerializer, \
                                WorkSerializer
from django.db.models import Q
from .query_language import parse as parse_query


class LibraryPagination(PageNumberPagination):
    """ Class for pagination
        gives current page number and last page number
    """
    def get_paginated_response(self, data):
        return Response({
                'current': self.page.number,
                'last': self.page.paginator.num_pages,
                'count': self.page.paginator.count,
                'results': data,
            })


class SongList(ListCreateAPIView):
    """ Class for listing songs
    """
    serializer_class = SongSerializer
    pagination_class = LibraryPagination

    def get_queryset(self):
        """ Search and filter the songs
        """
        # if 'query' is in the query string
        # then perform search
        if 'query' in self.request.query_params:
            query = self.request.query_params.get('query', None)
            if query:
                # the query can use a syntax, the query language, to specify
                # which term to search where
                # the language manages the simple search as well
                # the parser is provided from query_language.py
                res = parse_query(query)
                q = []
                q_many = []
                # specific terms of the research, i.e. artists, works and titles
                for artist in res['artists']:
                    q_many.append(Q(artists__name__icontains=artist))
                for artist in res['artists_exact']:
                    q_many.append(Q(artists__name__iexact=artist))
                for work in res['works']:
                    q.append(Q(works__title__icontains=work))
                for work in res['works_exact']:
                    q.append(Q(works__title__iexact=work))
                for title in res['titles']:
                    q.append(Q(title__icontains=title))
                for title in res['titles_exact']:
                    q.append(Q(title__iexact=title))
                # unspecific terms of the research
                for remain in res['remaining']:
                    q.append(
                            Q(title__icontains=remain) |
                            Q(artists__name__icontains=remain) |
                            Q(works__title__icontains=remain)
                        )

                # tags
                for tag in res['tags']:
                    q_many.append(Q(tags__name=tag))

                # now, gather the query objects
                filter_query = Q()
                for item in q:
                    filter_query &= item

                query_set = Song.objects.filter(filter_query)
                # gather the query objects involving custom many to many relation
                for item in q_many:
                    query_set = query_set.filter(item)

                # saving the parsed query to give it back to the client
                self.query_parsed = res

                return query_set.distinct().order_by(Lower('title'))

        # otherwise return all songs
        return Song.objects.all().order_by(Lower('title'))

    def list(self, request, *args, **kwargs):
        """ Send a listing of songs
        """
        response = super(SongList, self).list(request, args, kwargs)

        # pass the query words to highlight to the response
        # the words have been passed to the object in the get_queryset method
        # now, they have to be passed to the response
        # this is why this function in overloaded
        if hasattr(self, 'query_parsed'):
            response.data['query'] = self.query_parsed

        return response


class SongDetailView(RetrieveUpdateDestroyAPIView):
    """ Class for displaying song details
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer


class ArtistList(ListCreateAPIView):
    """ Class for listing artists
    """
    queryset = Artist.objects.all().order_by("name")
    serializer_class = ArtistSerializer
    pagination_class = LibraryPagination


class WorkList(ListCreateAPIView):
    """ Class for listing works
    """
    queryset = Work.objects.all().order_by("title", "subtitle")
    serializer_class = WorkSerializer
    pagination_class = LibraryPagination
