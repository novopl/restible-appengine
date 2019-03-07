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
from typing import List, Optional, Text, Tuple, Type, Union

# 3rd party imports
from restible import (
    RawResponse,
    RestEndpoint,
    RestResource,
)
from six import iteritems   # pylint: disable=wrong-import-order

# GAE bundled imports
import webapp2
from google.appengine.api import users


HandlerClass = Type[webapp2.RequestHandler]
ResourceClass = Type[RestResource]
EndpointClass = Type[RestEndpoint]
ResourceMapping = Tuple[Text, ResourceClass]
RouteConf = namedtuple('RouteConf', 'anon auth admin')


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

        if self.find_action(action_name, generic, self.request.method):
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
        if request.body and request.content_type == 'application/json':
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
del FunctionType, List, Optional, Union
