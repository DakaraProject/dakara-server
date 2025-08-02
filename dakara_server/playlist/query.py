from django.db.models import Q

from library.models import WorkType
from library.query import gather_query, gather_query_many, make_songs_query_from_res
from library.query_language import QueryLanguageParser, regroup


def query_entries(query_set, query):
    """Create a queryset that filters playlist entries according to a query.

    Args:
        query_set (): Initial query set (containing all entries).
        query (str): Query string. It can follow the
            the query language, to specify which term
            to search and where, or be a simple
            pattern.

    Returns:
        tuple: Tuple of the filtered query set, and the
        parsed query.
    """
    work_types = [wt.query_name for wt in WorkType.objects.all()]
    language_parser = QueryLanguageParser(
        ["owner", "artist", "work", "title"] + work_types
    )
    res = regroup(language_parser.parse(query), "work_type", work_types)

    # query for song
    query_list, query_list_many = make_songs_query_from_res(res, "song__")

    # query for owner
    for owner in res["owner"]["contains"]:
        query_list.append(Q(owner__username__icontains=owner))

    for owner in res["owner"]["exact"]:
        query_list.append(Q(owner__username__iexact=owner))

    # gather the query objects
    query_set_filtered = gather_query_many(
        gather_query(query_set, query_list), query_list_many
    )

    return query_set_filtered, res
