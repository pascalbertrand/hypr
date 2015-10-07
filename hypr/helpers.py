"""
hypr.helpers
------------

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


import itertools
import re


pattern = re.compile('(<([a-zA-Z0-9_]+(\(.*\))?:|)([a-zA-Z0-9_]*)>)')


def _rule_mangling(key, *urls):
    # A helper to tansform variable segment of an URL rule list by mangling
    # variable names from `variable` to `key_variable` and avoid conflicts.
    #
    # Example::
    #
    #   >>> _rule_mangling('/groups/<id>/users/<filter("ok"):value>', 'name')
    #   /groups/<name_id>/users/<filter("ok"):name_value>

    return tuple(re.sub(pattern, r'<\2_%s__\4>' % key, u) for u in urls)


def _rule_mpxing(*args):
    # Multiplexing a list of tuple
    # (A, B), (a, b), (0, 1)

    suffixes = ()   # empty tuple
    for prefixes in reversed(args):

        if prefixes is None:
            continue

        pr = tuple(set(r.rstrip('/') for r in prefixes))
        sf = tuple(set('/%s' % r.lstrip('/') for r in suffixes))
        suffixes = tuple(''.join(r) for r in itertools.product(pr, sf)) or \
            pr or sf

    return suffixes

