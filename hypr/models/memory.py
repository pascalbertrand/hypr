"""
hypr.models.memorymodel
-----------------------

Implements an in-memory only data model.

It is not intended for real-life usages, it's not bullet-proof, it's not thread
safe and above all it's not well tested. Use it at your own risk but does not
expect more than a tool to test your code.

:copyright: (c) 2015 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


import copy
import inspect

from hypr.globals import current_app
from hypr.exc import ModelConflictException, ModelFilterException, \
    ModelSearchException
from hypr.models.base import BaseModel
from collections import defaultdict


COMMITTED_OBJ = defaultdict(lambda: dict())
PENDING_OBJ = defaultdict(lambda: dict())


class MemoryModel(BaseModel):
    """
    """

    def __init__(self, **kwargs):

        self._version = 0
        self._modified = False
        self._delete = False
        self._orig_uid = None

        pending = PENDING_OBJ[self.__class__.__name__]

        for name, value in kwargs.items():
            if inspect.isroutine(getattr(self, name, None)):
                raise ValueError('%s is a reserved name' % name)
            setattr(self, name, value)

        pending[self._uid()] = self

    def __setattr__(self, name, value):

        if name != '_modified' and getattr(self, name, None) != value:
            self._modified = True

        super().__setattr__(name, value)

    def _match(self, **kwargs):

        filters = getattr(self, '__filters__', None) # a tuple or None

        for k, v in kwargs.items():

            if not ((filters is None or k in filters) and hasattr(self, k)):
                raise ModelFilterException('Unknown filter `{}`'.format(k))

            if not isinstance(v, tuple):
                v = v,
            if hasattr(self, k) and getattr(self, k) in (v or (None,)):
                continue
            return False
        return True

    @classmethod
    def get(cls, _limit=0, _offset=0, _order=None, _search=None, **kwargs):

        # get the default and absolute limits of the application
        default_limit = 100
        absolute_limit = 100
        if current_app is not None:
            default_limit = current_app.config['COLLECTION_DEFAULT_MAX']
            absolute_limit = current_app.config['COLLECTION_ABSOLUTE_MAX']

        if _search:
            raise ModelSearchException()

        store = COMMITTED_OBJ[cls.__name__]
        resp = {k: copy.deepcopy(v) for k, v in store.items()
                                             if v._match(**kwargs)}

        limit = min(_limit or default_limit, absolute_limit)
        return list(resp.values())[_offset:_offset+limit]

    def save(self, commit=True):

        pending = PENDING_OBJ[self.__class__.__name__]
        pending[self._uid()] = self

        if commit:
            self.commit()

    def delete(self, commit=True):
        """
        Delete a specific instance.
        """

        pending = PENDING_OBJ[self.__class__.__name__]
        pending[self._uid()] = self

        self._delete = True

        if commit:
            self.commit()

    @classmethod
    def commit(cls):
        """
        Save all the pending instances.
        """

        store = COMMITTED_OBJ[cls.__name__]
        pending = PENDING_OBJ[cls.__name__]

        # increment object version and check for possible conflicts
        for k, v in pending.items():

            # the primary key has changed (this will create a conflicting
            # clone of the resource)
            if k != v._uid():
                raise ModelConflictException()

            # the version manipulated by the client and the database aren't
            # synced anymore.
            if k in store and store[k]._version != v._version:
                raise ModelConflictException()

            if v._modified:
                v._version += 1

        # delete marked objects
        to_delete = (k for k, v in pending.items() if v._delete)
        store.update(pending)
        for obj in to_delete:
            del store[obj]
        PENDING_OBJ.pop(cls.__name__, None)

    @classmethod
    def rollback(cls):

        PENDING_OBJ.pop(cls.__name__, None)

    @classmethod
    def reset(cls):
        """
        This method flush all stored and pending objects.
        """

        COMMITTED_OBJ.pop(cls.__name__, None)
        PENDING_OBJ.pop(cls.__name__, None)

