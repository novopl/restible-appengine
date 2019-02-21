# -*- coding: utf-8 -*-
# Copyright 2018-2019 Mateusz Klos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
""" Integration for Google AppEngine secure python scaffold. """
from __future__ import absolute_import, unicode_literals

# stdlib imports
from collections import namedtuple
from types import FunctionType
from typing import List, Text, Tuple, Type

# 3rd party imports
from restible import (
    RestEndpoint,
    RestResource,
)

# GAE bundled imports
import webapp2


HandlerClass = Type[webapp2.RequestHandler]
ResourceClass = Type[RestResource]
EndpointClass = Type[RestEndpoint]
ResourceMapping = Tuple[Text, ResourceClass]
RouteConf = namedtuple('RouteConf', 'anon auth admin')


def handler(base_cls, methods=None):
    # type: (HandlerClass, List[Text]) -> FunctionType
    """ A short-cut for defining routes as functions and not classes.

    Returns the given function wrapped inside a dynamically generated
    handler class that derives from the given *base_cls*. Only the selected
    methods ('get' by default) will be implemented and will just call the
    function wrapped by this decorator.

    The wrapped function will receive an instance of the generated handler as
    it's only argument. You can use the handler passed in the ``handler``
    argument the same way you would use ``self`` inside a regular class
    based webapp2 handler.

    Args:
        base_cls (Type[app.base.BaseHandler]):
            A handler class to use as a base class for the generated wrapper
            handler.
        methods (list[str]):
            A list of HTTP methods that should be allowed on this handler.

    Returns:
        A class based handler that just calls the function wrapped by this
        decorator.

    Examples:

        >>> from app.base import handlers
        >>>
        >>> @handler(handlers.AuthenticatedAjaxHandler)
        ... def my_route(handler):
        ...     handler.response.set_status(200)
        ...     handler.render_json({"msg": "hello, world"})

    """
    methods = methods or ['get']

    def decorator(fn):                  # pylint: disable=missing-docstring
        wrapper = type(fn.__name__, (base_cls,), {})
        wrapper.wrapped_view = fn

        # Only add methods that are allowed.
        for http_method in methods:
            method_name = webapp2._normalize_handler_method(http_method)
            setattr(
                wrapper,
                method_name,
                lambda self, *args, **kw: self.wrapped_view(*args, **kw)
            )

        return wrapper

    return decorator


# Used only by type hint comments.
del FunctionType, List
