"""
hypr.app
--------

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""

import asyncio

from aiohttp.web import Application
from .dispatcher import Dispatcher
from .globals import LocalStorage
from .testing import TestClient


class Hypr(Application):
    """
    """

    def __init__(self, *, logger=None, loop=None, router=None,
                 handler_factory=None, middlewares=None):

        if loop is None:
            loop = asyncio.get_event_loop()

        kwargs = {'logger': logger,
                  'loop': loop,
                  'router': router or Dispatcher(),
                  'handler_factory': handler_factory,
                  'middlewares': middlewares}

        super().__init__(**{k: v for k, v in kwargs.items() if v is not None})

        # create the local storage for upcoming tasks binded to the app

        LocalStorage.bind(self)

    def propagate(self):

        self.router.propagate(self)

    def test_client(self):

        return TestClient(self)

    def run(self, host=None, port=None, debug=None, **options):
        """
        Run the application on a local server.
        """

        loop = self.loop
        host = host or '127.0.0.1'
        port = port or 5555

        handler = self.make_handler()
        f = loop.create_server(handler, host, port)

        srv = loop.run_until_complete(f)

        # TODO: better logging
        print('Listening on ', host, ':', port)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(handler.finish_connections(1.0))
            srv.close()
            loop.run_until_complete(srv.wait_closed())
            loop.run_until_complete(self.finish())
        loop.close()
