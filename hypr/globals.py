"""
hypr.globals
------------

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""

import tasklocals
from functools import partial


class LocalStorage:

    _app = None
    _task = None

    @classmethod
    def bind(cls, app):
        cls._app = app
        cls._task = tasklocals.local(loop=app.loop)

    def app(self):
        return self._app

    def set(self, name, attr):

        if self._task is None:
            raise RuntimeError('LocalStorage is not binded to an application')

        setattr(self._task, name, attr)

    def get(self, name, default=...):

        if self._task is None:
            raise RuntimeError('LocalStorage is not binded to an application')

        rv = getattr(self._task, name, default)

        if rv is Ellipsis:
            raise KeyError(name)

        return rv

    def delete(self, name):

        if self._task is None:
            raise RuntimeError('LocalStorage is not binded to an application')

        delattr(self._task, name)

class Proxy:

    def __init__(self, proxy):
        self._proxy = proxy

    def __getattr__(self, attr):
        proxy = self._proxy()
        return getattr(proxy, attr)

    def __repr__(self):
        proxy = self._proxy()
        return proxy.__repr__()


request = Proxy(partial(LocalStorage().get, 'request'))
current_app = Proxy(partial(LocalStorage().app))
