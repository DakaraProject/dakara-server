from django.db.models import Q


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


def gather_query_remain(query_set, query_list_remain):
    # now, gather the query objects
    filter_query = Q()
    for item in query_list_remain:
        filter_query |= item

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
