"""
hypr.web_exceptions
-------------------

Implements two helper functions to easily throw aiohttp's web exceptions from
their associated status code.

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""

from aiohttp.web_exceptions import *


error_codes = {

    # 3xx redirection

    300: HTTPMultipleChoices,
    301: HTTPMovedPermanently,
    302: HTTPFound,
    303: HTTPSeeOther,
    304: HTTPNotModified,
    305: HTTPUseProxy,
    307: HTTPTemporaryRedirect,

    # 4xx client error

    400: HTTPBadRequest,
    401: HTTPUnauthorized,
    402: HTTPPaymentRequired,
    403: HTTPForbidden,
    404: HTTPNotFound,
    405: HTTPMethodNotAllowed,
    406: HTTPNotAcceptable,
    407: HTTPProxyAuthenticationRequired,
    408: HTTPRequestTimeout,
    409: HTTPConflict,
    410: HTTPGone,
    411: HTTPLengthRequired,
    412: HTTPPreconditionFailed,
    413: HTTPRequestEntityTooLarge,
    414: HTTPRequestURITooLong,
    415: HTTPUnsupportedMediaType,
    416: HTTPRequestRangeNotSatisfiable,
    417: HTTPExpectationFailed,

    # 5xx server error

    500: HTTPInternalServerError,
    501: HTTPNotImplemented,
    502: HTTPBadGateway,
    503: HTTPServiceUnavailable,
    504: HTTPGatewayTimeout,
    505: HTTPVersionNotSupported,

}


def abort(code, *args, **kwargs):
    """
    Abort the request processing and return an error to the client.
    """

    if code in range(400,418) or code in range(500,506):
        raise error_codes[code](*args, **kwargs)

    raise HTTPInternalServerError()


def redirect(location, code=302):
    """
    Stop the request processing and return a redirection to a specified
    location to the client.
    """

    if code in range(300, 308):
        raise error_codes[code](location)

    raise HTTPInternalServerError()
