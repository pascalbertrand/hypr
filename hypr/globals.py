"""
hypr.globals
------------

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""

import tasklocals
from functools import partial


class LocalStorage:

    _storage = None

    @classmethod
    def bind(cls, app):
        cls._storage = tasklocals.local(loop=app.loop)

    def set(self, name, attr):
        return setattr(self._storage, name, attr)

    def get(self, attr):
        return getattr(self._storage, attr)


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
