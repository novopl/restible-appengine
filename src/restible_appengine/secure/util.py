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
from typing import List, Optional, Text, Tuple, Type, Union

# 3rd party imports
from restible import (
    RestEndpoint,
    RestResource,
)

# GAE bundled imports
import webapp2

# local imports
from .endpoint import GaeSecureMixin


HandlerClass = Type[webapp2.RequestHandler]
ResourceClass = Type[RestResource]
EndpointClass = Type[RestEndpoint]
ResourceMapping = Tuple[Text, ResourceClass]
RouteConf = namedtuple('RouteConf', 'anon auth admin')


class RestRouteBuilder(object):
    """ A simple tool for building secure scaffold compatible route definitions

    Examples:

        >>> from restible_appengine import secure
        >>> from app.base import handlers
        >>> from app import resources
        >>>
        >>> rest_route = secure.RestRouteBuilder(
        ...     anon_handler=handlers.BaseAjaxHadler,
        ...     auth_handler=handlers.AuthenticatedAjaxHandler,
        ...     admin_handler=handlers.AdminAjaxHandler,
        ... )
        >>>
        >>> _UNAUTHENTICATED_AJAX_ROUTES = [
        ...     rest_route('/api/user/signup', resources.UserResource,
        ...                login=False),
        ... ]
        >>>
        >>> _AJAX_ROUTES = [
        ...     rest_route('/api/user', resources.UserResource),
        ...     rest_route('/api/user/<user_pk>', resources.UserResource),
        ... ]

    """
    def __init__(self, anon_handler, auth_handler, admin_handler):
        # type: (HandlerClass, HandlerClass, HandlerClass) -> None
        self.anon_handler = anon_handler
        self.auth_handler = auth_handler
        self.admin_handler = admin_handler

    def __call__(self, url, res_cls, login=True, name=None):
        # type: (Text, ResourceClass, Union[bool, Text]) -> webapp2.Route
        """ Create a route definition for the given URL.

        Args:
            url (str):
                The URL template as implemented in `webapp2.Route`.
            res_cls (ResourceClass):
                The resource class to use for the endpoint.
            login (Union[bool, str]):
                Whether this route should be accessible by anonymous,
                authenticated or admin users.

        Returns:
            webapp2.Route: A new route definition ready to include in your
                webapp2 routing configuration.
        """
        if login is True:
            base_cls = self.auth_handler
        elif login == 'admin':
            base_cls = self.admin_handler
        else:
            base_cls = self.anon_handler

        return webapp2.Route(url, handler=endpoint(base_cls, res_cls), name=name)


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

    Examples:

        >>> from restible_appengine import secure
        >>> from webapp2 import Route
        >>> from app.base import handlers
        >>> from app import resources
        >>>
        >>> _AJAX_ROUTES = [
        ...     Route('/user', handler=secure.endpoint(
        ...         handlers.AuthenticatedAjaxHandler,
        ...         resources.UserResource
        ...     )),
        ...     Route('/user/<user_pk>', handler=secure.endpoint(
        ...         handlers.AuthenticatedAjaxHandler,
        ...         resources.UserResource
        ...     ))
        ... ]

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


# Used only by type hint comments.
del FunctionType, List, Optional, Union
