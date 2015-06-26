=========================
 InThe.AM API for Python
=========================

.. image:: https://img.shields.io/travis/aperezdc/intheam-python.svg?style=flat
   :target: https://travis-ci.org/aperezdc/intheam-python
   :alt: Build Status

.. image:: https://img.shields.io/coveralls/aperezdc/intheam-python/master.svg?style=flat
   :target: https://coveralls.io/r/aperezdc/intheam-python?branch=master
   :alt: Code Coverage

Python client module for the `Inthe.AM <https://inthe.am/>`_
`REST API <http://intheam.readthedocs.org/en/latest/api/index.html>`_:

.. code-block:: python

    import asyncio, intheam, os

    def print_task_list_ids(result):
        for task in (yield from result):
            print(task.uuid)

    api = intheam.InTheAm(os.getenv("INTHEAM_API_TOKEN"))
    asyncio.get_event_loop().run_until_complete(
        print_task_list_ids(api.pending()))


Installation
============

The stable releases are uploaded to `PyPI <https://pypi.python.org>`_, so you
can install them and upgrade using ``pip``::

  pip install intheam

Alternatively, you can install development versions —at your own risk—
directly from the Git repository::

  pip install -e git://github.com/aperezdc/intheam-python


Documentation
=============

There is no documentation for now. In the meanwhile, please read the source
code.


Development
===========

If you want to contribute, please use the usual GitHub workflow:

1. Clone the repository.
2. Hack on your clone.
3. Send a pull request for review.

If you do not have programming skills, you can still contribute by `reporting
issues <https://github.com/aperezdc/intheam-python/issues>`_ that you may
encounter.
