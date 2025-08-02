from django.db.models import Q

from library.models import WorkType
from library.query_language import QueryLanguageParser, regroup


def query(prefix, name, value):
    """Shorthand to make a query with the Q object and a prefix.

    Args:
        prefix (str or None): If truthy, prepended to `name`.
        name (str): Name of the field.
        value (str): Value for the field in the query.

    Returns:
        django.db.models.Q: Query.
    """
    if prefix:
        return Q(**{prefix + name: value})

    return Q(**{name: value})


def gather_query(query_set, query_list):
    """Filter a query set by elements of a query list.

    Args:
        query_set: Initial query set.
        query_list (list of django.db.models.Q): List of queries.

    Returns:
        New firtered query set.
    """
    # now, gather the query objects
    filter_query = Q()
    for item in query_list:
        filter_query &= item

    # gather the query objects for usual relations
    return query_set.filter(filter_query)


def gather_query_many(query_set, query_list_many):
    """Filter a query set by elements of a query list of many to many fields.

    Args:
        query_set: Initial query set.
        query_list (list of django.db.models.Q): List of queries for many to
        many fields.

    Returns:
        New firtered query set.
    """
    query_set_filtered = query_set

    # gather the query objects for custom many to many relation
    for item in query_list_many:
        query_set_filtered = query_set_filtered.filter(item)

    return query_set_filtered


def make_songs_query_from_res(res, prefix=None):
    """Make a query for songs.

    Args:
        res (dict): Dictionary on research terms, parsed.
        prefix (str or None): Optional prefix to add when creating the query.

    Returns:
        tuple of list: List of  queries, and list of queries targeting many to
        many relations.
    """
    query_list = []
    query_list_many = []

    # specific terms of the research, i.e. artists, works and titles
    for artist in res["artist"]["contains"]:
        query_list_many.append(query(prefix, "artists__name__icontains", artist))

    for artist in res["artist"]["exact"]:
        query_list_many.append(query(prefix, "artists__name__iexact", artist))

    for title in res["title"]["contains"]:
        query_list.append(query(prefix, "title__icontains", title))

    for title in res["title"]["exact"]:
        query_list.append(query(prefix, "title__iexact", title))

    for work in res["work"]["contains"]:
        query_list.append(
            query(prefix, "works__title__icontains", work)
            | query(prefix, "works__alternative_title__title__icontains", work)
        )

    for work in res["work"]["exact"]:
        query_list.append(
            query(prefix, "works__title__iexact", work)
            | query(prefix, "works__alternative_title__title__iexact", work)
        )

    # specific terms of the research derivating from work
    for query_name, search_keywords in res["work_type"].items():
        for keyword in search_keywords["contains"]:
            query_list.append(
                (
                    query(prefix, "works__title__icontains", keyword)
                    | query(
                        prefix, "works__alternative_title__title__icontains", keyword
                    )
                )
                & query(prefix, "works__work_type__query_name", query_name)
            )

        for keyword in search_keywords["exact"]:
            query_list.append(
                (
                    query(prefix, "works__title__iexact", keyword)
                    | query(prefix, "works__alternative_title__title__iexact", keyword)
                )
                & query(prefix, "works__work_type__query_name", query_name)
            )

        # one may want to factor the duplicated query on the work type
        # but it is very unlikely someone will define severals animes
        # (by instance) for a song at the same time
        # IMHO a factorization will make the code less clear and just
        # heavier, for no practical reason

    # unspecific terms of the research
    for remain in res["remaining"]:
        query_list.append(
            query(prefix, "title__icontains", remain)
            | query(prefix, "artists__name__icontains", remain)
            | query(prefix, "works__title__icontains", remain)
            | query(prefix, "works__alternative_title__title__icontains", remain)
            | query(prefix, "version__icontains", remain)
            | query(prefix, "detail__icontains", remain)
            | query(prefix, "detail_video__icontains", remain)
        )

    # tags
    for tag in res["tag"]:
        query_list_many.append(query(prefix, "tags__name", tag))

    return query_list, query_list_many


def query_songs(query_set, query):
    """Create a queryset that filters songs according to query.

    Args:
        query_set (): Initial query set (containing all songs).
        query (str): Query string. It can follow the
            the query language, to specify which term
            to search and where, or be a simple
            pattern.

    Returns:
        tuple: Tuple of the filtered query set, and the
        parsed query.
    """
    work_types = [wt.query_name for wt in WorkType.objects.all()]
    language_parser = QueryLanguageParser(["artist", "work", "title"] + work_types)
    res = regroup(language_parser.parse(query), "work_type", work_types)

    # query
    query_list, query_list_many = make_songs_query_from_res(res)

    # gather the query objects
    query_set_filtered = gather_query_many(
        gather_query(query_set, query_list), query_list_many
    )

    return query_set_filtered, res


def query_artists(query_set, query):
    """Create a queryset that filters artists according to query.

    Args:
        query_set (): Initial query set (containing all artists).
        query (str): Query string. It can only be a simple pattern (no query language).

    Returns:
        tuple: Tuple of the filtered query set, and the
        parsed query.
    """
    # using query language parser to split terms and for uniformity
    res = QueryLanguageParser.split_remaining(query)
    query_list = []
    # only unspecific terms are used
    for remain in res:
        query_list.append(Q(name__icontains=remain))

    # gather the query objects
    query_set_filtered = gather_query(query_set, query_list)

    return query_set_filtered, res


def query_works(query_set, query):
    """Create a queryset that filters works according to query.

    Args:
        query_set (): Initial query set (containing all works).
        query (str): Query string. It can only be a simple pattern (no query language).

    Returns:
        tuple: Tuple of the filtered query set, and the
        parsed query.
    """
    # using query language parser to split terms and for uniformity
    res = QueryLanguageParser.split_remaining(query)
    query_list = []
    # only unspecific terms are used
    for remain in res:
        query_list.append(
            Q(title__icontains=remain)
            | Q(subtitle__icontains=remain)
            | Q(alternative_title__title__icontains=remain)
        )

    # gather the query objects
    query_set_filtered = gather_query(query_set, query_list)

    return query_set_filtered, res
