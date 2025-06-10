from django.db.models import Q

from library.query_language import QueryLanguageParser


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
    language_parser = QueryLanguageParser()
    res = language_parser.parse(query)
    query_list = []
    query_list_many = []
    # specific terms of the research, i.e. artists, works and titles
    for artist in res["artist"]["contains"]:
        query_list_many.append(Q(artists__name__icontains=artist))

    for artist in res["artist"]["exact"]:
        query_list_many.append(Q(artists__name__iexact=artist))

    for title in res["title"]["contains"]:
        query_list.append(Q(title__icontains=title))

    for title in res["title"]["exact"]:
        query_list.append(Q(title__iexact=title))

    for work in res["work"]["contains"]:
        query_list.append(
            Q(works__title__icontains=work)
            | Q(works__alternative_title__title__icontains=work)
        )

    for work in res["work"]["exact"]:
        query_list.append(
            Q(works__title__iexact=work)
            | Q(works__alternative_title__title__iexact=work)
        )

    # specific terms of the research derivating from work
    for query_name, search_keywords in res["work_type"].items():
        for keyword in search_keywords["contains"]:
            query_list.append(
                (
                    Q(works__title__icontains=keyword)
                    | Q(works__alternative_title__title__icontains=keyword)  # noqa E501
                )
                & Q(works__work_type__query_name=query_name)
            )

        for keyword in search_keywords["exact"]:
            query_list.append(
                (
                    Q(works__title__iexact=keyword)
                    | Q(works__alternative_title__title__iexact=keyword)
                )
                & Q(works__work_type__query_name=query_name)
            )

        # one may want to factor the duplicated query on the work type
        # but it is very unlikely someone will define severals animes
        # (by instance) for a song at the same time
        # IMHO a factorization will make the code less clear and just
        # heavier, for no practical reason

    # unspecific terms of the research
    for remain in res["remaining"]:
        query_list.append(
            Q(title__icontains=remain)
            | Q(artists__name__icontains=remain)
            | Q(works__title__icontains=remain)
            | Q(works__alternative_title__title__icontains=remain)
            | Q(version__icontains=remain)
            | Q(detail__icontains=remain)
            | Q(detail_video__icontains=remain)
        )

    # tags
    for tag in res["tag"]:
        query_list_many.append(Q(tags__name=tag))

    # now, gather the query objects
    filter_query = Q()
    for item in query_list:
        filter_query &= item

    # gather the query objects for usual relations
    query_set_filtered = query_set.filter(filter_query)
    # gather the query objects for custom many to many relation
    for item in query_list_many:
        query_set_filtered = query_set_filtered.filter(item)

    return query_set_filtered, res


def query_artists(query_set, query):
    """Create a queryset that filters artists according to query.

    Args:
        query_set (): Initial query set (containing all songs).
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
    filter_query = Q()
    for item in query_list:
        filter_query &= item

    query_set_filtered = query_set.filter(filter_query)

    return query_set_filtered, res
