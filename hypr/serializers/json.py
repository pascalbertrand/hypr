"""
    hypr.serializers.json
    ---------------------

    Convert input object to raw JSON.

    :copyright: (c) 2014 by Morgan Delahaye-Prat.
    :license: BSD, see LICENSE for more details.
"""


import json


def encoder(obj):
    """
    """

    # handle date[time] objects

    if hasattr(obj, 'strftime'):
        if hasattr(obj, 'hour'):
            return obj.isoformat()
        else:
            return '%sT00:00:00' % obj.isoformat()

    # handle uuid objects
    if hasattr(obj, 'hex'):
        return str(obj)

    # handle serializable objects

    if hasattr(obj, '__serialize__'):
        return obj.__serialize__()

    raise TypeError('%s is not JSON serializable.' % repr(obj))



def json_serializer(obj, pretty_print=False, default=None):
    """
    """

    indent = None
    if pretty_print:
        indent = 4

    if default is None:
        default=encoder

    return json.dumps(obj, default=default, sort_keys=True, indent=indent)
