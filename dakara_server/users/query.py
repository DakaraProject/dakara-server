from django.db.models import Q

from internal.query import gather_query_remain
from library.query_language import QueryLanguageParser


def query_users(query_set, query):
    """Create a queryset that filters users according to a query.

    Args:
        query_set (): Initial query set (containing all users).
        query (str): Query string. It can follow the
            the query language, to specify which term
            to search and where, or be a simple
            pattern.

    Returns:
        tuple: Tuple of the filtered query set, and the
        parsed query.
    """
    # using query language parser to split terms and for uniformity
    res = QueryLanguageParser.split_remaining(query)

    query_list_remain = []
    # only unspecific terms are used
    for remain in res:
        query_list_remain.append(Q(username__icontains=remain))

    # gather the query objects
    query_set_filtered = gather_query_remain(query_set, query_list_remain)

    return query_set_filtered, {"remaining": res}
