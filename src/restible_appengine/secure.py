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
import itertools
from urlparse import urljoin
from typing import List, Optional, Tuple

# 3rd party imports
from restible import RestEndpoint, RawResponse, api_action
from six import iteritems

# GAE bundled imports
import webapp2
from google.appengine.api import users


class GaeSecureMixin(RestEndpoint):
    """ Mixin to use as base of endpoint classes. """
    def __init__(self, *args, **kw):
        super(GaeSecureMixin, self).__init__(self.res_cls, *args, **kw)

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

    def custom_dispatch(self, *args, **kw):
        """ Override webapp2 dispatcher. """
        self.request.rest_keys = self.request.route_kwargs

        result = self.call_rest_handler(self.request.method, self.request)
        return self.response_from_result(result)

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


def build_urls(api_urls):
    """ Create a list of webapp2 handlers for the given url mapping.

    Args:
        api_urls (list[tuple[str, RestResource]]):
            A list of URL mapping in the form ``(url, ResourceClass)``.

    Returns:
        list[webapp2.Route]: Webapp2 URL config.

    Example:

        >>> routes = build_urls([
        ...     ('/api/user', UserResource),
        ...     ('/api/post', BlogPostResource)
        ... ])

    """
    return list(itertools.chain.from_iterable((
        _build_endpoint(base_url, res_cls_) for base_url, res_cls_ in api_urls
    )))


def _build_endpoint(base_url, res_cls_):
    base_cls_anon = BaseAjaxHandler
    base_cls_auth = AuthenticatedAjaxHandler
    base_cls = base_cls_auth

    class ResourceEndpoint(base_cls, GaeSecureMixin):
        """ Auto generated endpoint class. Custom for each endpoint. """
        res_cls = res_cls_

        def __init__(self, *args, **kw):
            base_cls.__init__(self, *args, **kw)
            GaeSecureMixin.__init__(self)

    return _endpoint_urls(
        url=base_url,
        base_cls_anon=base_cls_anon,
        base_cls_auth=base_cls_auth,
        endpoint_cls=ResourceEndpoint,
    )


def _endpoint_urls(base_cls_anon, base_cls_auth, endpoint_cls, url, **opts):
    if not url.endswith('/'):
        url += '/'

    if not hasattr(endpoint_cls, 'resource'):
        endpoint_cls.resource = endpoint_cls.res_cls()

    urls = []
    url_list = url
    url_item = urljoin(url, r'<{}_pk>/'.format(endpoint_cls.resource.name))

    # Add urls for all actions
    for action in endpoint_cls.resource.rest_actions():
        meta = api_action.get_meta(action)
        base_url = url_list if meta.generic else url_item
        handler = build_action_handler(
            base_cls_auth if meta.protected else base_cls_anon,
            endpoint_cls.resource,
            action
        )

        urls += [webapp2.Route(
            name='{}-{}'.format(endpoint_cls.resource.name, meta.name),
            template=urljoin(base_url, meta.name),
            handler=handler,
            methods=[x.upper() for x in meta.methods],
            defaults={
                'name': meta.name
            }
        )]

    # Add CRUD urls
    urls += [
        webapp2.Route(
            name='{}-item'.format(endpoint_cls.resource.name),
            template=url_item[:-1],
            handler=endpoint_cls,
            handler_method='custom_dispatch',
            methods=['GET', 'PUT', 'DELETE'],

        ),
        webapp2.Route(
            name='{}-list'.format(endpoint_cls.resource.name),
            template=url_list[:-1],
            handler=endpoint_cls,
            methods=['GET', 'POST'],
        ),
    ]

    return urls


def build_action_handler(base_cls, resource_, action_):
    """ Build a webapp handler for the given action. """
    class SecureActionHandler(base_cls, GaeSecureMixin):
        """ Auto generated webapp2 handler for resource actions. """

        action = action_
        resource = resource_

        def custom_dispatch(self):
            """ Override webapp2 dispatcher. """
            self.request.rest_keys = self.request.route_kwargs

            action_meta = api_action.get_meta(self.action)
            result = self.call_action_handler(
                self.request.method,
                self.request,
                action_meta.name,
                action_meta.generic
            )
            return self.response_from_result(result)

    return SecureActionHandler

# Used only by type hint comments. Will be dropped if GAE ever moves to python 3
del List, Optional, Tuple
