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

from hypr.exc import ModelConflictException
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

    @classmethod
    def get(cls, _limit=0, _offset=0, _order=None, _search=None, **kwargs):
        """
        Retrieve multiple instances of the class.
        """

        store = COMMITTED_OBJ[cls.__name__]
        pending = PENDING_OBJ[cls.__name__]

        resp = {k: copy.deepcopy(v) for k, v in store.items()
                                             if v.match(**kwargs)}
        pending.update(resp)

        if _limit > 0:
            return list(resp.values())[_offset:_offset+_limit]
        else:
            return list(resp.values())

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

    def delete(self):
        """
        Delete a specific instance.
        """

        self._delete = True

    def match(self, **kwargs):
        """
        Verify if an instance match the filters passed as kwargs.
        """

        for k, v in kwargs.items():
            if hasattr(self, k) and getattr(self, k) in (v or (None,)):
                continue
            return False
        return True
