"""
hypr.testing
-------------

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


from aiohttp import request
import asyncio
import socket


def _find_unused_port():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestClient:

    def __init__(self, app):

        self.app = app
        self.srv = None
        self.handler = self.app.make_handler()

    def __enter__(self):

        self.port = _find_unused_port()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self.srv is not None:
            self.srv.close()
            self.app.loop.run_until_complete(self.handler.finish_connections())
            self.srv = None

    @asyncio.coroutine
    def create_server(self):

        self.srv = yield from self.app.loop.create_server(
            self.handler,'127.0.0.1', self.port)

    def request(self, method, path, **kwargs):

        kwargs['loop'] = self.app.loop

        @asyncio.coroutine
        def do_request():

            if self.srv is None:
                yield from self.create_server()

            url = 'http://127.0.0.1:{}'.format(self.port) + path
            rv = yield from request(method, url, **kwargs)
            rv.text = yield from rv.text()

            return rv

        return self.app.loop.run_until_complete(do_request())

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def head(self, url, **kwargs):
        return self.request('HEAD', url, **kwargs)

    def options(self, url, **kwargs):
        return self.request('OPTIONS', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def put(self, url, **kwargs):
        return self.request('PUT', url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request('PATCH', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

