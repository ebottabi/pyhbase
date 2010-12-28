PyHBase
=======

Python client for the HBase Avro interface, supporting both synchronous and asynchronous ([Tornado](http://tornadoweb.org/)-based) modes of operation.

Installation
------------

This project is [available on PyPI](http://pypi.python.org/pypi/PyHBase/).

To install, run:

    $ sudo pip install pyhbase

Alternatively, to build directly from source, run:

    $ sudo python setup.py install

HBase Avro Gateway
------------------

The HBase Avro Gateway is available in HBase 0.9x, and in the HBase 0.2x [hbase-trunk-with-avro](http://github.com/hammer/hbase-trunk-with-avro) fork.

To start the Avro Gateway:

    $ $HBASE_HOME/bin/hbase-daemon.sh start avro

Usage
-----

Synchronous usage example:

    >>> from pyhbase.connection import HBaseConnection
    >>> sc = HBaseConnection('localhost', 9090)
    >>> sc.create_table('test_table', 'cf1', 'cf2')
    >>> sc.put('test_table', 'key1', 'cf1:qualifier1', 'value1')
    >>> sc.get('test_table', 'key1')
    {u'entries': [{u'value': 'value1', u'qualifier': 'qualifier1', u'family': 'cf1', u'timestamp': 1293494506843}], u'row': 'key1'}

Asynchronous usage example:

    >>> from pyhbase.connection import AsyncHBaseConnection
    >>> from tornado.ioloop import IOLoop
    >>> ac = AsyncHBaseConnection('localhost', 9090)
    >>> def on_response(response):
    ...     print response
    ...     IOLoop.instance().stop()
    ...
    >>> ac.get('test_table', 'key1', callback=on_response)
    >>> IOLoop.instance().start()
    {u'entries': [{u'value': 'value1', u'qualifier': 'qualifier1', u'family': 'cf1', u'timestamp': 1293494506843}], u'row': 'key1'}

Note that administrative operations (`create_table`, `alter`, `truncate`, `flush`, etc.) are not available from the asynchronous client.
