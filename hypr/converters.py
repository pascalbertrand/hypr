"""
hypr.converters
---------------

Based on the work of Armin Ronacher for Flask.

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""

import re
import uuid


class BaseConverter:
    """Base class for all converters."""

    regex = '[^/]+'
    weight = 100

    def to_python(self, value):
        return value


class UnicodeConverter(BaseConverter):
    """This converter is the default converter and accepts any string but
    only one path segment.  Thus the string can not include a slash.
    This is the default validator.
    Example::
        Rule('/pages/<page>'),
        Rule('/<string(length=2):lang_code>')
    :param map: the :class:`Map`.
    :param minlength: the minimum length of the string.  Must be greater
                      or equal 1.
    :param maxlength: the maximum length of the string.
    :param length: the exact length of the string.
    """

    def __init__(self, minlength=1, maxlength=None, length=None):

        super().__init__()

        if length is not None:
            length = '{%d}' % int(length)
        else:
            if maxlength is None:
                maxlength = ''
            else:
                maxlength = int(maxlength)
            length = '{%s,%s}' % (int(minlength), maxlength)

        self.regex = '[^/]' + length


class AnyConverter(BaseConverter):
    """Matches one of the items provided.  Items can either be Python
    identifiers or strings::
        Rule('/<any(about, help, imprint, class, "foo,bar"):page_name>')
    :param map: the :class:`Map`.
    :param items: this function accepts the possible items as positional
                  arguments.
    """

    def __init__(self, *items):

        super().__init__()
        self.regex = '(?:%s)' % '|'.join([re.escape(x) for x in items])


class PathConverter(BaseConverter):
    """Like the default :class:`UnicodeConverter`, but it also matches
    slashes.  This is useful for wikis and similar applications::
        Rule('/<path:wikipage>')
        Rule('/<path:wikipage>/edit')
    :param map: the :class:`Map`.
    """

    regex = '[^/].*?'
    weight = 200


class NumberConverter(BaseConverter):
    """Baseclass for `IntegerConverter` and `FloatConverter`.
    :internal:
    """

    weight = 50

    def __init__(self, fixed_digits=0, min=None, max=None):

        super().__init__()
        self.fixed_digits = fixed_digits
        self.min = min
        self.max = max

    def to_python(self, value):

        if (self.fixed_digits and len(value) != self.fixed_digits):
            raise ValueError()
        value = self.num_convert(value)
        if (self.min is not None and value < self.min) or \
           (self.max is not None and value > self.max):
            raise ValueError()
        return value


class IntegerConverter(NumberConverter):
    """This converter only accepts integer values::
        Rule('/page/<int:page>')
    This converter does not support negative values.
    :param map: the :class:`Map`.
    :param fixed_digits: the number of fixed digits in the URL.  If you set
                         this to ``4`` for example, the application will
                         only match if the url looks like ``/0001/``.  The
                         default is variable length.
    :param min: the minimal value.
    :param max: the maximal value.
    """

    regex = r'\d+'
    num_convert = int


class FloatConverter(NumberConverter):
    """This converter only accepts floating point values::
        Rule('/probability/<float:probability>')
    This converter does not support negative values.
    :param map: the :class:`Map`.
    :param min: the minimal value.
    :param max: the maximal value.
    """

    regex = r'\d*\.\d+'
    num_convert = float

    def __init__(self, min=None, max=None):
        super().__init__(0, min, max)


class UUIDConverter(BaseConverter):
    """This converter only accepts UUID strings::
        Rule('/object/<uuid:identifier>')
    .. versionadded:: 0.10
    :param map: the :class:`Map`.
    """

    regex = r'[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-' \
            r'[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}'

    def to_python(self, value):
        return uuid.UUID(value)


DEFAULT_CONVERTERS = {
    'default':          UnicodeConverter,
    'string':           UnicodeConverter,
    'any':              AnyConverter,
    'path':             PathConverter,
    'int':              IntegerConverter,
    'float':            FloatConverter,
    'uuid':             UUIDConverter,
}
