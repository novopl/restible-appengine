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
"""
Base class for resources using Google AppEngine ndb as storage.
"""
from __future__ import absolute_import, unicode_literals

# stdlib imports
from logging import getLogger

# 3rd party imports
from serafin import Fieldspec
from six import iteritems   # pylint: disable=wrong-import-order

# local imports
from restible.model import ModelResource
from restible import util


L = getLogger(__name__)


class NdbResource(ModelResource):
    """ Base class for ndb based resources.

    This provides a basic implementation that can be used out of the box. It
    provides no authentication/authorization.
    """
    name = None
    model = None
    spec = Fieldspec('*')
    schema = {}

    def create_item(self, request, values):
        item = self.model(**values)
        item.put()

        return item

    def update_item(self, request, values):
        item = self.get_item(request)

        if item is None:
            return None

        values.pop('id', None)
        util.update_from_values(item, values)
        item.put()

        return item

    def delete_item(self, request, item):
        item.delete()

    def query_items(self, request, filters):
        """ Return a model query with the given filters.

        The query can be further customised like any ndb query.

        :return google.appengine.ext.ndb.Query:
            The query with the given filters already applied.
        """
        filters = [getattr(self.model, n) == v for n, v in iteritems(filters)]
        return self.model.query().filter(*filters)

    def get_item(self, request):
        pk = self.get_pk(request)
        return self.model.get_by_id(int(pk))
