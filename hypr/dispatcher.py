"""
hypr.dispatcher
---------------

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


import asyncio
import re
from aiohttp import hdrs
from aiohttp.abc import AbstractRouter, AbstractMatchInfo
from aiohttp.protocol import HttpVersion11
from hypr.web_exceptions import HTTPMethodNotAllowed, HTTPNotFound, \
                                HTTPInternalServerError, HTTPTemporaryRedirect
from aiohttp.web import Response
from hypr.converters import DEFAULT_CONVERTERS
from hypr.provider import Provider
from hypr.globals import LocalStorage
from hypr.serializers import json_serializer


__all__ = ('Dispatcher', 'Rule')


_rule_re = re.compile(r'''
    (?P<static>[^<]*)                           # static rule data
    <
    (?:
        (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)   # converter name
        (?:\((?P<args>.*?)\))?                  # converter arguments
        \:                                      # variable delimiter
    )?
    (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)        # variable name
    >
''', re.VERBOSE)

_converter_args_re = re.compile(r'''
    ((?P<name>\w+)\s*=\s*)?
    (?P<value>
        True|False|
        \d+.\d+|
        \d+.|
        \d+|
        \w+|
        [urUR]?(?P<stringval>"[^"]*?"|'[^']*')
    )\s*,
''', re.VERBOSE | re.UNICODE)

_PYTHON_CONSTANTS = {
    'None':     None,
    'True':     True,
    'False':    False
}


def _pythonize(value):
    if value in _PYTHON_CONSTANTS:
        return _PYTHON_CONSTANTS[value]
    for convert in int, float:
        try:
            return convert(value)
        except ValueError:
            pass
    if value[:1] == value[-1:] and value[0] in '"\'':
        value = value[1:-1]
    return str(value)


def get_converter(converter_name, args, kwargs):
    """Looks up the converter for the given parameter."""

    err_msg = 'The converter {!r} does not exist'

    if converter_name not in DEFAULT_CONVERTERS:
        raise LookupError(err_msg.format(converter_name))
    return DEFAULT_CONVERTERS[converter_name](*args, **kwargs)


def parse_converter_args(argstr):
    """
    """
    argstr += ','
    args = []
    kwargs = {}

    for item in _converter_args_re.finditer(argstr):
        value = item.group('stringval')
        if value is None:
            value = item.group('value')
        value = _pythonize(value)
        if not item.group('name'):
            args.append(value)
        else:
            name = item.group('name')
            kwargs[name] = value

    return tuple(args), kwargs


def parse_rule(rule):
    """
    Parse a rule and return it as a generator. Each iteration yields tuples
    in the form ``(converter, arguments, variable)``. If the converter is
    `None` it's static url part, otherwise it's a dynamic one.
    """
    pos = 0
    end = len(rule)

    do_match = _rule_re.match
    used_names = set()

    while pos < end:
        match = do_match(rule, pos)
        if match is None:
            break
        data = match.groupdict()
        if data['static']:
            yield None, None, data['static']

        variable = data['variable']
        converter = data['converter'] or 'default'

        if variable in used_names:
            raise ValueError('variable name %r used twice.' % variable)
        used_names.add(variable)

        yield converter, data['args'] or None, variable
        pos = match.end()

    if pos < end:
        remaining = rule[pos:]
        if '>' in remaining or '<' in remaining:
            raise ValueError('malformed url rule: %r' % rule)
        yield None, None, remaining


# compatibility with asyncio.web original Application
@asyncio.coroutine
def _defaultExpectHandler(request):
    """Default handler for Except: 100-continue"""
    if request.version == HttpVersion11:
        request.transport.write(b'HTTP/1.1 100 Continue\r\n\r\n')


class MatchInfo(dict, AbstractMatchInfo):

    def __init__(self, match_dict, rule, provider):
        super().__init__(match_dict)
        self._provider = provider
        self._rule = rule

    @property
    def route(self):
        return self._rule

    @property
    def handler(self):

        def ensure_response(request):

            rv = yield from self._provider.local_dispatcher(request)

            status_or_headers = headers = None
            if isinstance(rv, tuple):
                rv, status_or_headers, headers = rv + (None,) * (3 - len(rv))

            if rv is None:
                raise HTTPInternalServerError()

            if isinstance(status_or_headers, (list, dict)):
                headers, status_or_headers = status_or_headers, None

            if not isinstance(rv, Response):

                data = rv

                rv = Response(headers=headers, status=status_or_headers or 200,
                              content_type='application/json')

                rv.text = json_serializer(data)
                headers = status_or_headers = None

            if status_or_headers is not None:
                if isinstance(status_or_headers, int):
                    rv.status = status_or_headers

            if headers:
                rv.headers.extend(headers)

            return rv

        return ensure_response

    def __repr__(self):
        return "<MatchInfo {}: {}>".format(super().__repr__(), self.rule)


class Rule:

    def __init__(self, url, endpoint=None, methods=None, expect_handler=None):

        err_msg = 'Coroutine is expected, got {!r}'

        self.url = url
        self.endpoint = endpoint

        if methods is None:
            self.methods = hdrs.METH_ANY
        else:
            self.methods = set([m.upper() for m in methods])

        if expect_handler is None:
            expect_handler = _defaultExpectHandler
        assert asyncio.iscoroutinefunction(expect_handler), \
            err_msg.format(expect_handler)

        self.arguments = set()
        self.is_leaf = not url.endswith('/')
        self._trace = self._converters = self._regex = None

    def compile(self):
        """Compiles the regular expression and stores it."""

        self._trace = []
        self._converters = {}

        regex_parts = []

        def _build_regex(rule):

            for converter, arguments, variable in parse_rule(rule):
                if converter is None:
                    regex_parts.append(re.escape(variable))
                    self._trace.append((False, variable))
                else:
                    if arguments:
                        c_args, c_kwargs = parse_converter_args(arguments)
                    else:
                        c_args = ()
                        c_kwargs = {}
                    convobj = get_converter(converter, c_args, c_kwargs)
                    regex_parts.append('(?P<{}>{})'.format(variable,
                                                           convobj.regex))
                    self._converters[variable] = convobj
                    self._trace.append((True, variable))
                    self.arguments.add(str(variable))

        _build_regex(self.is_leaf and self.url or self.url.rstrip('/'))
        if not self.is_leaf:
            self._trace.append((False, '/'))

        regex = r'^{}{}$'.format(
            ''.join(regex_parts),
            not self.is_leaf and '(?<!/)(?P<__suffix__>/?)' or ''
        )

        self._regex = re.compile(regex, re.UNICODE)

    def match(self, path):
        """
        Check if the rule matches a given path.

        If the rule matches a dict with the converted values is returned,
        otherwise the return value is `None`.
        """

        m = self._regex.search(path)
        if m is not None:
            groups = m.groupdict()

            if not self.is_leaf and not groups.pop('__suffix__'):
                raise HTTPTemporaryRedirect(path + '/')

            result = {}
            for name, value in groups.items():
                try:
                    value = self._converters[name].to_python(value)
                except ValueError:
                    return
                result[str(name)] = value

            return result


class Dispatcher(AbstractRouter):

    def __init__(self):

        super().__init__()

        self._rules = []
        self._providers = {}

    @asyncio.coroutine
    def resolve(self, request):

        # initialize the local storage
        LocalStorage().set('request', request)

        path = request.path
        method = request.method

        allowed_methods = set()

        for rule in self._rules:
            match_dict = rule.match(path)

            if match_dict is None:
                continue

            if rule.methods == hdrs.METH_ANY or method in rule.methods:
                provider = self._providers[rule.endpoint]
                return MatchInfo(match_dict, rule, provider)

            allowed_methods.update(rule.methods)

        if allowed_methods:
            raise HTTPMethodNotAllowed(method, allowed_methods)
        else:
            raise HTTPNotFound()

    def add_provider(self, provider, *urls, endpoint=None, methods=None):
        """
        Register a provider for one or multiple given URLs.
        """

        err_msg = [
            'A Provider is required',
            'The endpoint {!r} already exists',
            'URL should be started with \'/\''
        ]

        # if the endpoint is not provided, use the name of the provider as the
        # endpoint
        if endpoint is None:
            endpoint = provider.name

        # if available methods are not specified, use the list of the
        # implemented methods in the provider.
        if methods is None:
            methods = provider.methods

        # some sanity checks
        assert issubclass(provider, Provider), err_msg[0]
        assert endpoint not in self._providers, err_msg[1].format(endpoint)

        for path in urls:
            if not path.startswith('/'):
                raise ValueError(err_msg[2])
            rule = Rule(path, endpoint, methods)
            rule.compile()

            self._rules.append(rule)

        if urls:
            self._providers[endpoint] = provider()

    def propagate(self, app):

        for endpoint, provider in dict(self._providers).items():
            for subrule in provider.iter_subrules(app, prefixes=tuple(self.iter_rules(endpoint))):
                entry = provider.__class__
                ep, urls, target = subrule
                self.add_provider(entry, *urls, endpoint=ep, methods=target.methods)

    def get_provider(self, endpoint):

        instance = self._providers.get(endpoint, None)

        if instance is not None:
            return instance.__class__

    def iter_rules(self, endpoint=None):

        return (rule.url for rule in self._rules if endpoint is None
                or rule.endpoint == endpoint)

