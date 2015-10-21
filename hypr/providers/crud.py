"""
hypr.providers.rest
-------------------

A RESTful provider.

:copyright: (c) 2015 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


from hypr.globals import request
from hypr.provider import Provider
from hypr.web_exceptions import abort
from hypr.exc import ModelConflictException


ERR_MSG = {
    'missing_uid': 'The provider `%s` requires a non trivial `_uid` method.',
}


def mini_dsl(args):
    """
    Parse a query string with the µDSL parser
    """

    parse = lambda param: tuple({v.strip() for v in param.split(',') if v})

    search = parse(args.get('_search', ''))
    order = parse(args.get('_order', ''))
    limit = int(args.get('_limit', 0))
    offset = int(args.get('_offset', 0))
    filters = {k: parse(v) for k, v in args.items() if not k.startswith('_')}

    return search, order, limit, offset, filters


class CRUDProvider(Provider):

    __model__ = None

    @classmethod
    def _uid(cls, **kwargs):
        """
        Returns the unique identifier of a resource based on the URL.
        """

        key = cls.__model__._key()
        uid = tuple(v for k, v in kwargs.items() if k in key)

        if len(uid) != len(key) or len(kwargs) != len(key):
            raise NotImplementedError(ERR_MSG['missing_uid'] % cls.__name__)

        return uid

    def get(self, **kwargs):

        model = self.__model__

        if len(kwargs):
            return model.one(*self._uid(**kwargs)) or abort(404)

        try:
            search, order, limit, offset, fltrs = mini_dsl(request.args)
        except ValueError:
            abort(400)

        count = model.count(_search=search, **fltrs)
        rv = model.get(limit, offset, order, search, **fltrs)

        return {
            'count': count,
            'result': rv,
        }

    def post(self):

        model = self.__model__
        bulk = request.args.get('_bulk', '').lower() in ['true', 'on', '1']
        json = yield from request.json()

        if json is None:
            abort(400)

        if not model.__validate__(json):
            abort(400)

        if bulk:
            # TODO: implement bulk POST
            raise NotImplementedError()
        else:
            rv = model(**json)

        # commit changes

        try:
            model.commit()
        except ModelConflictException:
            model.rollback()
            abort(409)
        else:
            return rv, 201

    def put(self, **kwargs):

        model = self.__model__
        bulk = request.args.get('_bulk', '').lower() in ['true', 'on', '1']
        json = yield from request.json()

        if json is None:
            abort(400)

        if not model.__validate__(json):
            abort(400)

        if bulk and not kwargs:
            # TODO: implement bulk PUT
            raise NotImplementedError()
        elif kwargs:

            rv = model.one(*self._uid(**kwargs)) or abort(404)
            for k, v in json.items():
                if hasattr(rv, k):
                    setattr(rv, k, v)
                else:
                    model.rollback()
                    abort(400)
        else:
            abort(400)

        # commit changes

        try:
            model.commit()
        except ModelConflictException:
            model.rollback()
            abort(409)
        else:
            return rv

    def delete(self, **kwargs):

        model = self.__model__
        bulk = request.args.get('_bulk', '').lower() in ['true', 'on', '1']

        if bulk and not kwargs:
            # TODO: implement bulk PUT
            raise NotImplementedError()
        elif kwargs:
            rv = model.one(*self._uid(**kwargs)) or abort(404)
            rv.delete()
        else:
            abort(400)

        # commit changes

        try:
            model.commit()
        except ModelConflictException:
            model.rollback()
            abort(409)
        else:
            return '', 204

