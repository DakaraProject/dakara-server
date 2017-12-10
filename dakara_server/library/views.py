from rest_framework.generics import (
        RetrieveUpdateDestroyAPIView,
        UpdateAPIView,
        ListCreateAPIView,
        ListAPIView,
        )

from django.db.models.functions import Lower
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Q

from . import models
from . import serializers
from .query_language import QueryLanguageParser


class LibraryPagination(PageNumberPagination):
    """Pagination

    Gives current page number and last page number
    """
    def get_paginated_response(self, data):
        return Response({
                'current': self.page.number,
                'last': self.page.paginator.num_pages,
                'count': self.page.paginator.count,
                'results': data,
            })


class SongListView(ListCreateAPIView):
    """List of songs
    """
    serializer_class = serializers.SongSerializer
    pagination_class = LibraryPagination

    def get_queryset(self):
        """Search and filter the songs
        """
        query_set = models.Song.objects.all()

        # hide all songs with disabled tags for non-managers or non-superusers
        user = self.request.user
        if not (user.is_superuser or user.has_library_permission_level('m')):
            query_set = query_set.exclude(tags__disabled=True)

        # if 'query' is in the query string then perform search otherwise
        # return all songs
        if 'query' not in self.request.query_params:
            return query_set.order_by(Lower('title'))

        query = self.request.query_params.get('query', None)
        if query:
            # the query can use a syntax, the query language, to specify which
            # term to search and where
            # the language manages the simple search as well the parser is
            # provided from query_language.py
            language_parser = QueryLanguageParser()
            res = language_parser.parse(query)
            q = []
            q_many = []
            # specific terms of the research, i.e. artists, works and titles
            for artist in res['artist']['contains']:
                q_many.append(Q(artists__name__icontains=artist))

            for artist in res['artist']['exact']:
                q_many.append(Q(artists__name__iexact=artist))

            for title in res['title']['contains']:
                q.append(Q(title__icontains=title))

            for title in res['title']['exact']:
                q.append(Q(title__iexact=title))

            for work in res['work']['contains']:
                q.append(Q(works__title__icontains=work))

            for work in res['work']['exact']:
                q.append(Q(works__title__iexact=work))

            # specific terms of the research derivating from work
            for query_name, search_keywords in res['work_type'].items():
                for keyword in search_keywords['contains']:
                    q.append(
                            Q(works__title__icontains=keyword) &
                            Q(works__work_type__query_name=query_name)
                            )

                for keyword in search_keywords['exact']:
                    q.append(
                            Q(works__title__iexact=keyword) &
                            Q(works__work_type__query_name=query_name)
                            )

                # one may want to factor the duplicated query on the work type
                # but it is very unlikely someone will define severals animes
                # (by instance) for a song at the same time
                # IMHO a factorization will make the code less clear and just
                # heavier, for no practical reason

            # unspecific terms of the research
            for remain in res['remaining']:
                q.append(
                        Q(title__icontains=remain) |
                        Q(artists__name__icontains=remain) |
                        Q(works__title__icontains=remain)
                    )

            # tags
            for tag in res['tag']:
                q_many.append(Q(tags__name=tag))

            # now, gather the query objects
            filter_query = Q()
            for item in q:
                filter_query &= item

            query_set = query_set.filter(filter_query)
            # gather the query objects involving custom many to many relation
            for item in q_many:
                query_set = query_set.filter(item)

            # saving the parsed query to give it back to the client
            self.query_parsed = res

        return query_set.distinct().order_by(Lower('title'))

    def list(self, request, *args, **kwargs):
        """Send a listing of songs
        """
        response = super().list(request, args, kwargs)

        # pass the query words to highlight to the response
        # the words have been passed to the object in the get_queryset method
        # now, they have to be passed to the response
        # this is why this function in overloaded
        if hasattr(self, 'query_parsed'):
            response.data['query'] = self.query_parsed

        return response


class SongView(RetrieveUpdateDestroyAPIView):
    """Edition and display of a song
    """
    queryset = models.Song.objects.all()
    serializer_class = serializers.SongSerializer


class ArtistListView(ListCreateAPIView):
    """List of artists
    """
    serializer_class = serializers.ArtistSerializer
    pagination_class = LibraryPagination

    def get_queryset(self):
        """ Search and filter the artists
        """
        query_set = models.Artist.objects.all()

        # if 'query' is in the query string then perform search return results
        # of the corresponding query
        if 'query' not in self.request.query_params:
            return query_set.order_by(Lower("name"))

        query = self.request.query_params.get('query', None)
        if query:
            # there is no need for query language for artists
            # it is used to split terms and for uniformity
            res = QueryLanguageParser.split_remaining(query)
            q = []
            # only unspecific terms are used
            for remain in res:
                q.append(
                        Q(name__icontains=remain)
                    )

            # gather the query objects
            filter_query = Q()
            for item in q:
                filter_query &= item

            query_set = query_set.filter(filter_query)
            # saving the parsed query to give it back to the client
            self.query_parsed = {'remaining': res}

        return query_set.order_by(Lower("name"))

    def list(self, request, *args, **kwargs):
        """ Send a listing of artists
        """
        response = super().list(request, args, kwargs)

        # pass the query words to highlight to the response
        # the words have been passed to the object in the get_queryset method
        # now, they have to be passed to the response
        # this is why this function in overloaded
        if hasattr(self, 'query_parsed'):
            response.data['query'] = self.query_parsed

        return response


class WorkListView(ListCreateAPIView):
    """ Class for listing works
    """
    serializer_class = serializers.WorkSerializer
    pagination_class = LibraryPagination

    def get_queryset(self):
        """ Search and filter the works
        """
        query_set = models.Work.objects.all()

        # if 'type' is in the query string
        # then filter work type
        if 'type' in self.request.query_params:
            work_type = self.request.query_params.get('type', None)
            if work_type:
                query_set = query_set.filter(work_type__query_name=work_type)

        # if 'query' is in the query string then perform search return results
        # of the corresponding query and type filter
        if 'query' not in self.request.query_params:
            return query_set.order_by(Lower("title"), Lower("subtitle"))

        query = self.request.query_params.get('query', None)
        if query:
            # there is no need for query language for works it is used to split
            # terms and for uniformity
            res = QueryLanguageParser.split_remaining(query)
            q = []
            # only unspecific terms are used
            for remain in res:
                q.append(
                        Q(title__icontains=remain) |
                        Q(subtitle__icontains=remain)
                    )

            # gather the query objects
            filter_query = Q()
            for item in q:
                filter_query &= item

            query_set = query_set.filter(filter_query)
            # saving the parsed query to give it back to the client
            self.query_parsed = {'remaining': res}

        return query_set.order_by(Lower("title"), Lower("subtitle"))

    def list(self, request, *args, **kwargs):
        """ Send a listing of works
        """
        response = super().list(request, args, kwargs)

        # pass the query words to highlight to the response
        # the words have been passed to the object in the get_queryset method
        # now, they have to be passed to the response
        # this is why this function in overloaded
        if hasattr(self, 'query_parsed'):
            response.data['query'] = self.query_parsed

        return response


class WorkTypeListView(ListCreateAPIView):
    queryset = models.WorkType.objects.all().order_by(Lower("name"))
    serializer_class = serializers.WorkTypeSerializer


class SongTagListView(ListAPIView):
    queryset = models.SongTag.objects.all().order_by(Lower("name"))
    serializer_class = serializers.SongTagSerializer
    pagination_class = LibraryPagination


class SongTagView(UpdateAPIView):
    queryset = models.SongTag.objects.all()
    serializer_class = serializers.SongTagSerializer
