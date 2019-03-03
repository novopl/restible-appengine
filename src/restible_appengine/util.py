# -*- coding: utf-8 -*-
""" Various helpers for easier/faster development. """
from __future__ import absolute_import, unicode_literals

# stdlib imports
from typing import Any, Dict, Text, Type

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
    ndb_filters = [getattr(model_cls, k) == v for k, v in iteritems(filters)]

    return model_cls.query().filter(*ndb_filters)


# Used only in type hint comments.
del Any, Dict, Text, Type, ndb
