"""
hypr.models.sqlalchemy
----------------------

:copyright: (c) 2015 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""

import inspect
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from hypr.exc import ModelConflictException, ModelFilterException, \
    ModelSearchException
from hypr.models.base import BaseModel
from hypr.globals import LocalStorage, current_app


locals = LocalStorage()
BaseSQLA = declarative_base()


def register_engine(conn_string):
    """
    """

    def decorator(cls):
        if hasattr(cls, 'register_engine'):
            cls.register_engine(conn_string)
        return cls

    return decorator


class SqlAlchemyModel(BaseSQLA, BaseModel):
    """
    """

    __abstract__ = True

    _session = None
    _engines = {}

    @classmethod
    def _key(cls):

        if getattr(cls, '__key__', None) is not None:
            rv = super()._key()
        else:
            rv = tuple(c.name for c
                              in sqlalchemy.orm.class_mapper(cls).primary_key)

        return rv

    @classmethod
    def _filter(cls, **kwargs):

        rv = []
        filters = getattr(cls, '__filters__', None) # a tuple or None

        for key, val in kwargs.items():

            if not ((filters is None or key in filters) and hasattr(cls, key)):
                raise ModelFilterException('Unknown filter `{}`'.format(key))

            if not isinstance(val, tuple):
                val = val,

            rv.append(sqlalchemy.or_(*{getattr(cls, key) == v for v in val}))

        return sqlalchemy.and_(*rv)

    @classmethod
    def _search(cls, val):

        rv = []
        search = getattr(cls, '__search__', None)   # a tuple or None

        if search is None:
            raise ModelSearchException()

        if not isinstance(search, tuple):
            search = search,

        if not isinstance(val, tuple):
            val = val,

        for key in search:
            rv.append(sqlalchemy.or_(
                *{getattr(cls, key).like('%{}%'.format(v)) for v in val}))

        return sqlalchemy.or_(*rv)

    @classmethod
    def _query_builder(cls, _search, _session, **kwargs):
        """
        A helper to build the SQL query from various parameters.
        """

        query = _session.query(cls)

        if kwargs:
            query = query.filter(cls._filter(**kwargs))

        if _search:
            query = query.filter(cls._search(_search))

        return query

    @classmethod
    def register_engine(cls, *args, **kwargs):
        """
        Bind the model with an engine.

        If conn_string is None, the default engine of the Hypr application is
        used.
        """

        if not args and not kwargs:
            args = current_app.config['MODELS_SQLALCHEMY_DEFAULT_SERVER'],

        engine = create_engine(*args, **kwargs)
        cls._engines[args[0]] = cls.metadata.bind = engine

    @classmethod
    def session(cls, context=False):
        """
        This class method returns a valid session.

        If this method is called in the context of a task, the method returns
        the active session if it exists or creates a new one and make it the
        active session. Outside of the context of a task, the method raises an
        exception unless `no_context` is set to ``True``.
        """

        if not context:
            rv = sessionmaker(bind=cls.metadata.bind)()
        else:
            rv = locals.get('sqlalchemy_session', None)
            if rv is None:
                rv = sessionmaker(bind=cls.metadata.bind)()
                locals.set('sqlalchemy_session', rv)

        return rv

    @classmethod
    def get(cls, _limit=0, _offset=0, _order=None, _search=None, _session=None,
            **kwargs):

        if _session is None:
            _session = cls.session(True)

        # get the default and absolute limits of the application
        default_limit = 100
        absolute_limit = 100
        if current_app is not None:
            default_limit = current_app.config['COLLECTION_DEFAULT_MAX']
            absolute_limit = current_app.config['COLLECTION_ABSOLUTE_MAX']

        query = cls._query_builder(_search, _session, **kwargs)

        if _order:
            if not isinstance(_order, tuple):
                _order = _order,

            for crit in _order:
                if crit.startswith('!'):
                    query = query.order_by(getattr(cls, crit[1:]).desc())
                else:
                    query = query.order_by(getattr(cls, crit))

        limit = min(_limit or default_limit, absolute_limit)
        return query.slice(_offset, _offset+limit).all()

    @classmethod
    def one(cls, *args, _session=None):

        col = cls._key()
        if _session is None:
            _session = cls.session(True)

        query = _session.query(cls)

        if len(col) != len(args):
            raise ValueError('Invalid key')

        # single primary key and no user-defined __key__
        if getattr(cls, '__key__', None) is None and len(col) == 1:
            return query.get(args[0])

        # make a zip of the col and _key lists
        return query.filter_by(**dict(zip(col, args))).first()

    @classmethod
    def count(cls, _search=None, _session=None, **kwargs):
        """
        """
        if _session is None:
            _session = cls.session(True)

        return cls._query_builder(_search, _session, **kwargs).count()

    def save(self, commit=True, _session=None):

        if _session is None:
            _session = self.session(True)

        _session.add(self)
        if commit:
            self.commit(_session)

    def delete(self, commit=True, _session=None):

        if _session is None:
            _session = self.session(True)

        _session.delete(self)
        if commit:
            self.commit(_session)

    @classmethod
    def commit(cls, _session=None):

        if _session is None:
            _session = cls.session(True)

        try:
            _session.commit()
        except sqlalchemy.exc.IntegrityError:
            raise ModelConflictException()

    @classmethod
    def rollback(cls, _session=None):
        if _session is None:
            _session = cls.session(True)

        _session.rollback()

    def __serialize__(self):

        return {k: v for k, v in inspect.getmembers(self)
                     if not k.startswith('_') and not inspect.isroutine(v)
                     and k not in ['metadata', 'query', 'query_class']}
