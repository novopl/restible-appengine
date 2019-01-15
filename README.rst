
restible-appengine
##################

.. readme_inclusion_marker


**restible-appengine** that allows you to use
`restible <https://github.com/novopl/restible>`_ in AppEngine standard python
environment. It includes a base resource class ``NdbResource`` that works as a
glue between *restible* and Datastore.

It also includes webapp2 integration for the secure scaffold (properly
integrates Google's base endpoint classes into
`restible <https://github.com/novopl/restible>`_.


.. note::
    The CircleCI builds can be found
    `here <https://circleci.com/gh/novopl/restible-appengine>`_

Installation
============

.. code-block:: shell

    $ pip install restible-appengine


Contributing
============

Cloning and setting up the development repo
-------------------------------------------

.. code-block:: shell

    $ git clone git@github.com:novopl/restible-appengine.git
    $ cd restible
    $ virtualenv env
    $ source ./env/bin/activate
    $ pip install .
    $ pip install -r ops/devrequirements.txt
    $ peltak git add-hooks

.. note::
    God knows why, installing the current package with
    ``python setup.py develop`` or ``python setup.py install`` will cause pylint
    to think **six** is a local project package and it will throw errors about
    the wrong import order.


Running tests
.............

.. code-block:: shell

    $ peltak test

Linting
.......

.. code-block:: shell

    $ peltak lint

Generating docs
...............

.. code-block:: shell

    $ peltak docs
