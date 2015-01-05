|Vanilla| Welcome to Vanilla Bean!
==================================

Obligatory Sinatra style (but concurrent!) micro-web framework for
`Vanilla <https://github.com/cablehead/vanilla>`__.

Example
-------

.. code:: python

    h = vanilla.Hub()
    b = h.bean(port=8000)

    @b.get('/')
    def index(request):
        response = request.response()
        response.send('Hello ')
        h.sleep(1000)
        response.send('World\n')

.. figure:: https://github.com/cablehead/vanilla.bean/raw/master/docs/images/terminal.gif
   :alt: terminal

Websockets
----------

.. code:: python

    h = vanilla.Hub()
    b = h.bean(port=8000)

    @b.websocket('/echo')
    def echo(ws):
        while True:
            ws.send(ws.recv())

Installation
------------

::

        pip install vanilla.bean


.. |Vanilla| image:: http://vanillapy.readthedocs.org/en/latest/_static/logo.png
