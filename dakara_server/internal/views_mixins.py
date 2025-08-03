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
