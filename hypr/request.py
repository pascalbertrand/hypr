"""
hypr.request
------------

:copyright: (c) 2015 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


import json
import asyncio

from aiohttp import hdrs
from aiohttp.abc import AbstractMatchInfo
from aiohttp.web import RequestHandler as BaseRequestHandler
from aiohttp.web_reqrep import Request as BaseRequest
from aiohttp.web import *


class Request(BaseRequest):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.m_filters = {}

    @asyncio.coroutine
    def json(self, *, loader=json.loads):

        body = yield from self.text()
        if body:
            return loader(body)
        return None


class RequestHandler(BaseRequestHandler):

    @asyncio.coroutine
    def handle_request(self, message, payload):
        if self.access_log:
            now = self._loop.time()

        app = self._app
        request = app.request_class(
            app, message, payload,
            self.transport, self.reader, self.writer,
            secure_proxy_ssl_header=self._secure_proxy_ssl_header)
        self._meth = request.method
        self._path = request.path

        try:
            match_info = yield from self._router.resolve(request)

            assert isinstance(match_info, AbstractMatchInfo), match_info

            resp = None
            request._match_info = match_info
            expect = request.headers.get(hdrs.EXPECT)
            if expect and expect.lower() == "100-continue":
                resp = (
                    yield from match_info.route.handle_expect_header(request))

            if resp is None:
                handler = match_info.handler
                for factory in reversed(self._middlewares):
                    handler = yield from factory(app, handler)
                resp = yield from handler(request)

            assert isinstance(resp, StreamResponse), \
                ("Handler {!r} should return response instance, "
                 "got {!r} [middlewares {!r}]").format(
                     match_info.handler, type(resp), self._middlewares)
        except HTTPException as exc:
            resp = exc

        resp_msg = resp.start(request)
        yield from resp.write_eof()

        # notify server about keep-alive
        self.keep_alive(resp_msg.keep_alive())

        # log access
        if self.access_log:
            self.log_access(message, None, resp_msg, self._loop.time() - now)

        # for repr
        self._meth = 'none'
        self._path = 'none'
