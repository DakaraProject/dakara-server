from django.db.models import Q

from internal.query import gather_query, gather_query_many, gather_query_remain, query
from library.models import WorkType
from library.query import make_songs_query_from_res
from library.query_language import QueryLanguageParser, regroup


def make_entries_query_from_res(res, prefix=None):
    """Make a query for playlist entries.

    Args:
        res (dict): Dictionary on research terms, parsed.
        prefix (str or None): Optional prefix to add when creating the query.

    Returns:
        tuple of list: List of  queries, and list of queries targeting many to
        many relations.
    """
    # query for song
    query_list, query_list_remain, query_list_many = make_songs_query_from_res(
        res, (prefix or "") + "song__"
    )

    # query for owner
    for owner in res["owner"]["contains"]:
        query_list.append(query(prefix, "owner__username__icontains", owner))

    for owner in res["owner"]["exact"]:
        query_list.append(query(prefix, "owner__username__iexact", owner))

    # unspecific terms of the research
    for remain in res["remaining"]:
        query_list_remain.append(query(prefix, "owner__username__icontains", remain))

    return query_list, query_list_remain, query_list_many


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

    # query for entries
    query_list, query_list_remain, query_list_many = make_entries_query_from_res(res)

    # gather the query objects
    query_set_filtered = gather_query_many(
        gather_query_remain(gather_query(query_set, query_list), query_list_remain),
        query_list_many,
    )

    return query_set_filtered, res


def query_errors(query_set, query):
    """Create a queryset that filters player errors according to a query.

    Args:
        query_set (): Initial query set (containing all errors).
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
        ["message", "owner", "artist", "work", "title"] + work_types
    )
    res = regroup(language_parser.parse(query), "work_type", work_types)

    # query for entries
    query_list, query_list_remain, query_list_many = make_entries_query_from_res(
        res, "playlist_entry__"
    )

    # query for error message
    for message in res["message"]["contains"]:
        query_list.append(Q(error_message__icontains=message))

    for message in res["message"]["exact"]:
        query_list.append(Q(error_message__iexact=message))

    # unspecific terms of the research
    for remain in res["remaining"]:
        query_list_remain.append(Q(error_message__icontains=remain))

    # gather the query objects
    query_set_filtered = gather_query_many(
        gather_query_remain(gather_query(query_set, query_list), query_list_remain),
        query_list_many,
    )

    return query_set_filtered, res
