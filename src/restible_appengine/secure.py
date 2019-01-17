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
import json
from collections import namedtuple
from types import FunctionType
from typing import List, Optional, Text, Tuple, Type

# 3rd party imports
from restible import (
    RawResponse,
    RestEndpoint,
    RestResource,
)
from six import iteritems

# GAE bundled imports
import webapp2
from google.appengine.api import users


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
        class RouteHandler(base_cls):   # pylint: disable=missing-docstring
            pass

        wrapper = type(fn.__name__, (RouteHandler,), {})
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


def endpoint(base_cls, res_cls_):
    """ Dynamically create an endpoint class for use with GAE secure scaffold.

    Args:
        base_cls (HandlerClass):
            The webapp2 handler class to be used as base for the endpoint
        res_cls_ (ResourceClass):
            The resource class this endpoint is handling.

    Returns:
        EndpointClass: A new endpoint class generated on the fly that inherits
            both the restible `RestEndpoint` (through `GaeSecureMixin`) and the
            given webapp2 handler class.
    """

    # pylint: disable=missing-docstring
    class ResourceHandlerClass(with_restible(base_cls)):
        res_cls = res_cls_

    return ResourceHandlerClass


def with_restible(base_handler_cls):
    """ A helper method to generate an endpoint base class.

    This will create a base handler class that derives from both the given
    base class and `GaeSecureMixin`

    Example:

        >>> from restible_appengine.secure import with_restible
        >>> from app.base.handlers import AuthenticatedAjaxHandler
        >>>
        >>> class MyHandler(with_restible(AuthenticatedAjaxHandler)):
        ...     res_cls = MyResource

    """

    # pylint: disable=missing-docstring
    class HandlerClass(base_handler_cls, GaeSecureMixin):
        def __init__(self, *args, **kw):
            base_handler_cls.__init__(self, *args, **kw)
            GaeSecureMixin.__init__(self)

    return HandlerClass


class GaeSecureMixin(RestEndpoint):
    """ Mixin to use as base of endpoint classes. """
    def __init__(self, *args, **kw):
        super(GaeSecureMixin, self).__init__(self.res_cls, *args, **kw)

    def get(self, *args, **kw):
        """ Forward webapp2 GET handler to custom_dispatch(). """
        return self.custom_dispatch(*args, **kw)

    def post(self, *args, **kw):
        """ Forward webapp2 POST handler to custom_dispatch(). """
        return self.custom_dispatch(*args, **kw)

    def put(self, *args, **kw):
        """ Forward webapp2 PUT handler to custom_dispatch(). """
        return self.custom_dispatch(*args, **kw)

    def delete(self, *args, **kw):
        """ Forward webapp2 DELETE handler to custom_dispatch(). """
        return self.custom_dispatch(*args, **kw)

    def custom_dispatch(self, *args, **kw):
        """ A custom request dispatcher.

        We need to go through the dispatch() -> METHOD() -> custom_dispatch()
        call stack just so we don't loose everything that's implemented in
        dispatch() by the secure scaffold.
        """
        self.request.rest_keys = self.request.route_kwargs

        action_name = self.request.path.rstrip('/').rsplit('/', 1)[-1]
        generic = not self.resource.get_pk(self.request)

        if self.find_action(action_name, generic):
            result = self.call_action_handler(
                self.request.method,
                self.request,
                action_name,
                generic
            )
        else:
            result = self.call_rest_handler(self.request.method, self.request)

        return self.response_from_result(result)

    def authorize(self, request):
        # type: (webapp2.Request) -> Optional[users.User]
        """ Return a user for an incoming request

        Args:
            request (webapp2.Request):
                The incoming request.

        Returns:
            users.User: User instance if we can find a user for this request.
            None: If not user can be assigned to this request. Equivalent to
                anonymous.
        """
        del request     # unused in this implementation
        return users.get_current_user()

    @classmethod
    def extract_request_data(cls, request):
        """ Extract request payload as JSON. """
        if request.body:
            return json.loads(request.body)

    def response_from_result(self, result):
        """ Generate webapp2 response from  RestResult.

        :param RestResult result:
            RestResult instance with the API call result.
        """
        if not isinstance(result, RawResponse):

            for name, value in iteritems(result.headers):
                self.response.headers[name] = value

            self.response.set_status(result.status)
            self.render_json(result.data)


# Used only by type hint comments.
del FunctionType, List, Optional
