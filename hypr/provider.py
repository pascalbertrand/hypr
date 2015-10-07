"""
hypr.provider
-------------

Implements the base provider in charge of providing the resources associated
to specific HTTP requests along with tools to customize their security
behavior.

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""

import asyncio
import inspect
import uuid

from hypr.helpers import _rule_mangling, _rule_mpxing
from hypr.globals import request


HTTP_METHODS = frozenset(['get', 'post', 'head', 'options', 'delete', 'put',
                          'trace', 'patch'])


def _endpoint_uuid(path):
    # To reach a resource by propagation, the request go through a list of
    # providers via named rules. Each route is unique and can be seen as an URL
    # provider0.rule0/provider1.rule1 ... and so on.
    #
    # This URL is then derived via SHA1 to an UUID (RFC 4122) to be used as the
    # endpoint of the rule.

    url = '/'.join(tuple('.'.join((p.__name__, r)) for p, r in path))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, url))


def checkpoint(scope=None):
    """
    ``checkpoint`` is a method decorator to enable a :class:`Provider`'s
    method as a security checkpoint.

    Security checkpoints are used to verify if user-defined prerequisites are
    met and, if not, block further request processing by raising an exception.

    The decorated method is responsible of the error raising (:func:`abort` is
    the prefered way to fulfill this task). To achieve this, the method is also
    able to read the current rule variable segments.

    :param scope: limit the scope of a security checkpoint.
                  (default: ``Provider.ALWAYS``)

        The following values are allowed for `scope`:

        .. tabularcolumns:: |p{3.5cm}|p{9.5cm}|

        ========================= =============================================
        :attr:`Provider.ALWAYS`   the checkpoint is always executed
        :attr:`Provider.ENTRY`    the checkpoint is executed when the provider
                                  is the first one of the processing chain
        :attr:`Provider.PATH`     the checkpoint is executed when the provider
                                  is part of the processing chain but isn't the
                                  entry-point of the processing
        :attr:`Provider.TRANSFER` the checkpoint is executed when the provider
                                  is part of the processing chain but isn't the
                                  last of it.
        :class:`str`              the checkpoint is executed for the specified
                                  propagation rule
        :class:`tuple`            any combination of the previous values
        ========================= =============================================

    Usages::

        class MyProvider(Provider):

            propagation_rules = {
                'rule0': OtherProvider0,
                'rule1': OtherProvider0,
            }

            @checkpoint     # equivalent to @checkpoint(scope=Provider.ALWAYS)
            def check_example(self, request):
                ...

            @checkpoint(scope=Provider.ENTRY)
            def check_login(self, request):
                ...

            @checkpoint(scope=('rule0','rule1'))
            def check_allowed(self):
                ...

    """

    if hasattr(scope, '__call__'):
        setattr(scope, '__hypr_cp', None)
        return scope
    else:
        def decorator(fn):
            setattr(fn, '__hypr_cp', scope)
            return fn

        return decorator


def filter(key=None, scope=None, requires=None):
    """
    ``filter`` is a decorator method to enable a :class:`Provider`'s method
    as a mandatory filter.

    Mandatory filters are used to limit the content of the response of the next
    provider when the processing is propagated to the latter. The goal is to
    prevent the use of a propagation rule as a workaround to bypass security
    checkpoint and to leak restricted data to unintended users.

    The effective filtering is handled by the next provider of the processing
    chain, the filter only associates the returned value of the method to a
    ``key`` and is stored in ``request.m_filters`` as a ``dict``. A filter
    returning ``None`` is ignored and does not affect ``request.m_filters``::

        @filter('key')
        def simple_filter(self):
            ...

    Some variable parts of the rule can be required to execute the filter.
    Those parts are, most of the time, determined from the method signature but
    in certain circumstances those segments can be manually specified with the
    ``requires`` argument of ``filter``::

        @filter('key', requires='value')
        def get(self, value=None):
            ...

    If more than one url parts are required, ``requires`` also accepts the
    ``tuples`` of string as valid arguments.

    :param key:   the key of the mandatory filter returned value.
    :param scope: limit the filter to a rule or a subset of rules.
                  (default: ``Provider.ALWAYS``)

        The following types are allowed for `scope`:

        .. tabularcolumns:: |p{3.5cm}|p{9.5cm}|

        ======================= ===============================================
        :attr:`Provider.ALWAYS` the filter is applied for any sub-rule
        :class:`str`            the filter is applied for the named sub-rule
        :class:`tuple`          a tuple of ``str`` to specify multiple sub-rule
                                at once
        ======================= ===============================================

    :param requires: specify required variable parts of the rule.
                     (default: ``None``)

        The following types are allowed for `scope`:

        .. tabularcolumns:: |p{3.5cm}|p{9.5cm}|

        ======================= ===============================================
        `None`                  the required parts are determined from the
                                method signature
        :class:`str`            the required variable part name
        :class:`tuple`          a tuple of ``str`` to specify multiple variable
                                part name at once
        ======================= ===============================================
    """

    if not isinstance(scope, tuple):
        scope = scope,

    if not (requires is None or isinstance(requires, tuple)):
        requires = requires,

    if hasattr(key, '__call__'):
        setattr(key, '__hypr_fltr', (scope, requires, None))
        return key
    else:
        def decorator(fn):
            setattr(fn, '__hypr_fltr', (scope, requires, key))
            return fn

        return decorator


class ProviderType(type):
    """
    """

    def __new__(mcs, name, bases, d):

        cls = type.__new__(mcs, name, bases, d)
        cls.name = name

        methods = set(cls.methods or [])
        sec_scope = {}

        fltrs = {}

        parents = inspect.getmembers(cls, inspect.isfunction)
        for name, func in parents:

            if name in HTTP_METHODS:
                methods.add(name.upper())

            # search filter methods
            hypr_fltr = getattr(func, '__hypr_fltr', None)
            if hypr_fltr is not None:
                for scope in hypr_fltr[0]:
                    if scope not in fltrs:
                        fltrs[scope] = set()
                    fltrs[scope].add((name,) + hypr_fltr[1:])

            # search security checkpoint methods
            hypr_sec = getattr(func, '__hypr_cp', ())
            if not isinstance(hypr_sec, tuple):
                hypr_sec = hypr_sec,
            for scope in hypr_sec:
                if scope not in sec_scope:
                    sec_scope[scope] = set()
                sec_scope[scope].add(name)

        cls.methods = tuple(methods)
        cls._sec_scope = sec_scope
        cls._fltrs = fltrs
        cls._subrules = {}
        return cls


class Provider(metaclass=ProviderType):
    """
    How to define propagation rules
    -------------------------------

    The propagation rules are internal rules of a provider to define a link
    between it and another and allowing the automatic generation of derived URL
    rules to access a resource through the security checks and the filters of
    all the intermediate providers.

    Each rule is defined with a tuple and stored in the
    :attr:`propagation_rules` (which is a dictionary). The syntax is as
    follow::

        propagation_rule = {
            `name`: (`target_provider`, `suffix0`, `suffix1`, ..., `suffixN`),
        }

    The `target_provider` can be a :class:`Provider` class or a :class:`str`
    where the value is the name of a registered :class:`Provider`. All the
    following terms of the :class:`tuple` are :class:`str` and will be appended
    to all the URL rules of the current provider. Any number of suffixes can
    be supplied, even zero. But, if there isn't any suffix, the default rules
    of the registered `target_provider` is used. The `name` is used to retrieve
    the target provider when the request is processed.

    A cycle detection mechanism prevents the possibilities of infinite URLs.
    """

    # pre-defined scope values accepted by @checkpoint

    ENTRY = 1           # the security decorated method is executed when the
                        # provider is the entry point of the method.
    PATH = 2            # the security decorated method is executed when the
                        # provider is on the path to access the resource and is
                        # not the entry-point provider (the final provider is
                        # in the path scope.
    TRANSFER = 3        # the security decorated method is executed when the
                        # provider transfer the processing to another provider.
    ALWAYS = None       # the security decorated method is always executed.

    name = None
    methods = None
    _sec_scope = _fltrs = _subrules = None

    propagation_rules = {}

    @classmethod
    def _url_filtering(cls, urls, scope, entry):

        # this private method limit a tuple of URL to a subset of it, based on
        # the applied filters.

        args = ()

        for name, requires, _ in cls._fltrs.get(scope, ()):

            if requires is None:
                meth = getattr(cls, name)
                requires = inspect.getargspec(meth)[0][1:]
            args += tuple(requires)

        if not entry:
            args = tuple('_{}__{}'.format(cls.name, a) for a in args)

        return tuple(u for u in urls if all(a in u for a in args))

    @classmethod
    def iter_subrules(cls, app, path=None, prefixes=None):
        """
        Return an iterable of URL subrules available from the Provider. This
        method is dependant from the application and requires a preliminary
        registration for all the Providers used as propagation target.

        The format of each subrule is as follow::

            (endpoint, url0[, url1[, ...]])

        For example::

            ('7a7c9e9b-085b-5c65-acd7-0239ce457a98', '/B/subtarget')

        This method updates the local routing table of each provider accessed
        by a propagation subrule but the deterministic nature of the algorithm
        in use make this operation idempotent.

        :param app: An instance of the application in which the subrules are to
                    be generated.
        """

        err_msg = ['No valid endpoint {!r} has been found.',
                   'No URLs available to reach {!r}']

        entry = False
        if path is None:
            entry = True
            path = []

        for name, rule in cls.propagation_rules.items():

            _prefixes = cls._url_filtering(prefixes, None, entry)
            _prefixed = cls._url_filtering(_prefixes, name, entry)

            # the path list is used to keep track of the providers already
            # known to avoid cycles creating infinite URL rules and to generate
            # the endpoint of the rule.
            _path = list(path)
            _path.append((cls, name))

            # ensure the sub-rule is well formatted and the target provider
            # registered and accessible.
            if not isinstance(rule, tuple):
                rule = rule,

            target, *urls = rule

            if not isinstance(target, ProviderType):
                target = app.router.get_provider(target)
                assert target is not None, err_msg[0].format(rule[0])

            if target not in (p for p, _ in _path):

                endpoint = _endpoint_uuid(_path)
                if not urls:
                    urls = tuple(app.router.iter_rules(rule[0])) or \
                        tuple(app.router.iter_rules(target.name))

                urls = _rule_mangling(target.name, *urls)

                assert urls, err_msg[1].format(target.name)

                cls._subrules[endpoint] = name, target(), entry
                yield endpoint, _rule_mpxing(_prefixes, urls), target

                for endpoint, urls, final in target.iter_subrules(app, _path, urls):
                    cls._subrules[endpoint] = name, target(), entry
                    yield endpoint, _rule_mpxing(_prefixes, urls), final

    # TODO: implement the autobinding
    #@classmethod
    #def auto_bind(cls, model):
    #    """
    #    """
    #    err_msg = 'The provider {!r} does not support the autobinding feature.'
    #    assert NotImplementedError(err_msg.format(cls.name, model))

    @property
    def is_entry(self):
        ep = request.match_info.route.endpoint
        return (ep == self.name) or self._subrules.get(ep, (0, 0, False))[2]

    @asyncio.coroutine
    def _call_meth(self, name):

        args = request.match_info

        # Retrieve a method by its name and call it with a set of keyword
        # arguments defined from the method signature and a set of key-values.

        meth = getattr(self, name)
        req, _, kw, _ = inspect.getargspec(meth)

        # Filter out unwanted values from dynamic segments of the URL
        is_mangled = lambda key: '__' in key and key[0] == '_' and key[1] != '_'
        if self.is_entry:
            args = {k: v for k, v in args.items() if not is_mangled(k)}
        else:
            unmangle = '_{}__'.format(self.name)
            args = {k[len(unmangle):]: v for k, v in args.items()
                    if k.startswith(unmangle)}

        # ensure meth is a generator
        if (not asyncio.iscoroutinefunction(meth) and
                not inspect.isgeneratorfunction(meth)):
            meth = asyncio.coroutine(meth)

        if kw is None:
            rv = yield from meth(**{k: v for k, v in args.items() if k in req})
        else:
            rv = yield from meth(**args) # any kerword arguments is accepted

        return rv

    @asyncio.coroutine
    def _apply_cp(self, scope):

        # Apply all the sec checkpoints associated with the specified scope.

        for name in self._sec_scope.get(scope, ()):
            yield from self._call_meth(name)

    @asyncio.coroutine
    def _apply_filters(self, scope):

        filters = sorted(self._fltrs.get(scope, ()), key=lambda t: t[-1])
        for name, _, key in filters:

            if key is None:
                key = self.name

            request.m_filters[key] = yield from self._call_meth(name)


    @asyncio.coroutine
    def local_dispatcher(self, request):
        """
        """

        ep = request.match_info.route.endpoint
        rule, target, _ = self._subrules.get(ep, (None, None, False))

        yield from self._apply_cp(self.ALWAYS)
        if self.is_entry:
            yield from self._apply_cp(self.ENTRY)
        else:
            yield from self._apply_cp(self.PATH)

        if target is not None:
            yield from self._apply_cp(rule)
            yield from self._apply_cp(self.TRANSFER)
            yield from self._apply_filters(self.ALWAYS)
            yield from self._apply_filters(rule)
            rv = yield from target.local_dispatcher(request)
        else:
            rv = yield from self._call_meth(request.method.lower())

        return rv
