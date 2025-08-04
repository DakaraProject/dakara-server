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

    def perform_query(self, query_set, query_method):
        """Perform the query in the query set."""
        # if 'query' is in the query string then perform search otherwise
        # return all songs
        if "query" not in self.request.query_params:
            return query_set

        query = self.request.query_params.get("query", None)
        if query:
            # query the song and save the parsed query
            # to give it back to the client
            query_set, self.query_parsed = query_method(query_set, query)

        return query_set.distinct()


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
