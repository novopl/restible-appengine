# -*- coding: utf-8 -*-
""" Various helpers for easier/faster development. """
from __future__ import absolute_import, unicode_literals

# stdlib imports
from typing import Any, Dict, List, Text, Type

# 3rd party imports
from six import iteritems
from google.appengine.ext import ndb


def ndb_query_from_values(model_cls, filters):
    # type: (Type[ndb.Model], Dict[Text, Any]) -> ndb.Query
    """ Create ndb query from a filters dict.

    This is a helper function to simplify the final resource actions
    implementations. Makes adding filtering to the query handlers dead simple.

    Args:
        model_cls (Type[ndb.Model]):
            The model class to query.
        filters (dict[str, Any]):
            This will use the ``model_cls.query()``  to create the initial query
            and then it will add a filter based on the *filters* dict.

    Returns:
        ndb.Query:
            ndb query corresponding to the given filters dict.

    Examples:

        >>> from restible_appengine.util import ndb_query_from_values
        >>>
        >>> class Person(ndb.Model):
        ...     name = ndb.StringProperty()
        ...     age = ndb.IntegerProperty()
        >>>
        >>> filters = {
        ...     'name': 'John',
        ...     'age': 32
        ... }
        >>> person = ndb_query_from_values(Person, filters).get()

    """
    ndb_filters = _parse_qs_filter(model_cls, filters)

    return model_cls.query().filter(*ndb_filters)


def _parse_qs_filter(model_cls, qs_params):
    # type: (Type[ndb.Model], Dict[Text, Text]) -> List[Any]
    op_map = {
        'eq': lambda mdl, name, value: getattr(mdl, name) == value,
        'ne': lambda mdl, name, value: getattr(mdl, name) != value,
        'lt': lambda mdl, name, value: getattr(mdl, name) < value,
        'gt': lambda mdl, name, value: getattr(mdl, name) > value,
        'lte': lambda mdl, name, value: getattr(mdl, name) <= value,
        'gte': lambda mdl, name, value: getattr(mdl, name) >= value,
        'in': lambda mdl, name, value: getattr(mdl, name).IN(value),
    }

    ndb_filters = []
    for flt, value in iteritems(qs_params):
        parts = flt.rsplit('__', 1)
        if len(parts) == 2:
            name, op = parts
        else:
            op = 'eq'
            name = parts[0]

        op_fn = op_map.get(op)
        if not op_fn:
            raise ValueError("Invalid OP: {} in '{}'".format(op, flt))

        ndb_filters.append(op_fn(model_cls, name, value))
    return ndb_filters


# Used only in type hint comments.
del Any, Dict, List, Text, Type, ndb
