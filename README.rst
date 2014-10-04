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
    def index(request, response):
        response.send('Hello ')
        h.sleep(1000)
        return 'World.\n'

.. figure:: docs/images/terminal.gif
   :alt: terminal

Installation
------------

::

        pip install vanilla.bean


.. |Vanilla| image:: http://vanillapy.readthedocs.org/en/latest/_static/logo.png
