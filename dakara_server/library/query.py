from django.db.models import Q

from internal.query import gather_query, gather_query_many, gather_query_remain, q
from internal.query_language import QueryLanguageParser, regroup
from library.models import WorkType


def make_songs_query_from_res(res, prefix=None):
    """Make a query for songs.

    Args:
        res (dict): Dictionary of research terms, parsed. If `id` is in the
            query terms, only filter by it.
        prefix (str or None): Optional prefix to add when creating the query.

    Returns:
        tuple of list: List of queries, list of remaining queries, and list of
        queries targeting many to many relations.
    """
    # query for id
    # optional and terminal
    # same behavior for contains and exact
    if (res_id := res.pop("id", None)) and (
        ids := res_id["contains"] + res_id["exact"]
    ):
        query_list = []
        for id in ids:
            query_list.append(q(prefix, "id", int(id)))

        return query_list, [], []

    query_list = []
    query_list_remain = []
    query_list_many = []

    # specific terms of the research, i.e. artists, works and titles
    for artist in res["artist"]["contains"]:
        query_list_many.append(q(prefix, "artists__name__icontains", artist))

    for artist in res["artist"]["exact"]:
        query_list_many.append(q(prefix, "artists__name__iexact", artist))

    for title in res["title"]["contains"]:
        query_list.append(q(prefix, "title__icontains", title))

    for title in res["title"]["exact"]:
        query_list.append(q(prefix, "title__iexact", title))

    for work in res["work"]["contains"]:
        query_list.append(
            q(prefix, "works__title__icontains", work)
            | q(prefix, "works__alternative_title__title__icontains", work)
        )

    for work in res["work"]["exact"]:
        query_list.append(
            q(prefix, "works__title__iexact", work)
            | q(prefix, "works__alternative_title__title__iexact", work)
        )

    # specific terms of the research derivating from work
    for query_name, search_keywords in res["work_type"].items():
        for keyword in search_keywords["contains"]:
            query_list.append(
                (
                    q(prefix, "works__title__icontains", keyword)
                    | q(prefix, "works__alternative_title__title__icontains", keyword)
                )
                & q(prefix, "works__work_type__query_name", query_name)
            )

        for keyword in search_keywords["exact"]:
            query_list.append(
                (
                    q(prefix, "works__title__iexact", keyword)
                    | q(prefix, "works__alternative_title__title__iexact", keyword)
                )
                & q(prefix, "works__work_type__query_name", query_name)
            )

        # one may want to factor the duplicated query on the work type
        # but it is very unlikely someone will define severals animes
        # (by instance) for a song at the same time
        # IMHO a factorization will make the code less clear and just
        # heavier, for no practical reason

    # unspecific terms of the research
    # conjunction of all terms
    query_remain = Q()
    for remain in res["remaining"]:
        query_remain &= (
            q(prefix, "title__icontains", remain)
            | q(prefix, "artists__name__icontains", remain)
            | q(prefix, "works__title__icontains", remain)
            | q(prefix, "works__alternative_title__title__icontains", remain)
            | q(prefix, "version__icontains", remain)
            | q(prefix, "detail__icontains", remain)
            | q(prefix, "detail_video__icontains", remain)
        )

    query_list_remain.append(query_remain)

    # tags
    for tag in res["tag"]:
        query_list_many.append(q(prefix, "tags__name", tag))

    return query_list, query_list_remain, query_list_many


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
    language_parser = QueryLanguageParser(
        ["id", "artist", "work", "title"] + work_types
    )
    res = regroup(language_parser.parse(query), "work_type", work_types)

    # query
    query_list, query_list_remain, query_list_many = make_songs_query_from_res(res)

    # gather the query objects
    query_set_filtered = gather_query_many(
        gather_query_remain(gather_query(query_set, query_list), query_list_remain),
        query_list_many,
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

    query_list_remain = []
    # only unspecific terms are used
    for remain in res:
        query_list_remain.append(Q(name__icontains=remain))

    # gather the query objects
    query_set_filtered = gather_query_remain(query_set, query_list_remain)

    return query_set_filtered, {"remaining": res}


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

    query_list_remain = []
    # only unspecific terms are used
    for remain in res:
        query_list_remain.append(
            Q(title__icontains=remain)
            | Q(subtitle__icontains=remain)
            | Q(alternative_title__title__icontains=remain)
        )

    # gather the query objects
    query_set_filtered = gather_query_remain(query_set, query_list_remain)

    return query_set_filtered, {"remaining": res}


def query_song_tags(query_set, query):
    """Create a queryset that filters song tags according to query.

    Args:
        query_set (): Initial query set (containing all song tags).
        query (str): Query string. It can only be a simple pattern (no query
            language).

    Returns:
        tuple: Tuple of the filtered query set, and the parsed query.
    """
    # using query language parser to split terms and for uniformity
    res = QueryLanguageParser.split_remaining(query)

    query_list_remain = []
    # only unspecific terms are used
    for remain in res:
        query_list_remain.append(Q(name__icontains=remain))

    # gather the query objects
    query_set_filtered = gather_query_remain(query_set, query_list_remain)

    return query_set_filtered, {"remaining": res}
