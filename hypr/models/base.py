"""
hypr.models.base
----------------

:copyright: (c) 2015 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


import inspect


class BaseModel:

    @classmethod
    def _key(cls):
        """
        Returns a tuple of the object's properties used to determine is unique
        identifier.
        """

        if not hasattr(cls, '__key__'):
            raise NotImplementedError()

        if not isinstance(cls.__key__, tuple):
            return cls.__key__,
        return cls.__key__

    def _uid(self):
        """
        Returns the unique identifier of the object in the form of a tuple.
        """
        return tuple(getattr(self, k) for k in self._key())

    @classmethod
    def get(cls, _limit=0, _offset=0, _order=None, _search=None, **kwargs):
        """
        Retrieve a list of instance of the class. This method support
        filtering, searching, ordering and pagination (if allowed).
        """
        raise NotImplementedError()

    @classmethod
    def one(cls, *args):
        """
        Retrieve a unique instance of the class.

        :class:`BaseModel` implements a non-optimized version of :meth:`one`
        based on the :meth:`get` method. If the method is not able to trivially
        retrieve one and only one instance of the class, the exception
        ``NotImplementedError`` will be raised.
        """

        if len(args) == len(cls._key()):
            resp = cls.get(**dict(zip(cls._key(), ((v,) for v in args))))
            if len(resp) == 1:
                return resp[0]
            if len(resp) == 0:
                return None

        raise NotImplementedError()

    @classmethod
    def count(cls, _search=None, **kwargs):
        """
        Count the total number of instances of the class.

        :class:`BaseModel` implements a non-optimized version of :meth:`count`
        based on the :meth:`get` method.
        """

        return len(cls.get(_search=_search, **kwargs))

    @classmethod
    def commit(cls):
        """
        Make persistent all the staged modifications.
        """
        raise NotImplementedError()

    @classmethod
    def rollback(cls):
        """
        Cancel all the staged modifications.

        This method is called by the provider whenever something fails. Its
        implementation is not mandatory.
        """
        pass

    def delete(self):
        """
        """
        raise NotImplementedError()

    @classmethod
    def __validate__(cls, json):
        """
        """
        return True

    def __serialize__(self):
        """
        """

        return {k: v for k, v in inspect.getmembers(self)
                     if not k.startswith('_') and not inspect.isroutine(v)}
