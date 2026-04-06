from django.db.models import Q

from internal.query import gather_query, gather_query_remain
from internal.query_language import QueryLanguageParser


def make_users_query_from_res(res):
    """Make a query for users.

    Args:
        res (dict): Dictionary on research terms, parsed. If `id` is in the
            query terms, only filter by it.
        prefix (str or None): Optional prefix to add when creating the query.

    Returns:
        tuple of list: List of queries, and list of remaining queries.
    """
    # query for id
    # terminal
    # same behavior for contains and exact
    res_id = res.pop("id")
    if ids := res_id["contains"] + res_id["exact"]:
        query_list = []
        for id in ids:
            query_list.append(Q(id=int(id)))

        return query_list, []

    query_list_remain = []

    # only unspecific terms are used
    for remain in res["remaining"]:
        query_list_remain.append(Q(username__icontains=remain))

    return [], query_list_remain


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
    language_parser = QueryLanguageParser(["id"])
    res = language_parser.parse(query)

    # query for users
    query_list, query_list_remain = make_users_query_from_res(res)

    # gather the query objects
    query_set_filtered = gather_query_remain(
        gather_query(query_set, query_list), query_list_remain
    )

    return query_set_filtered, res
