"""
hypr.exc
--------

Hypr exceptions.

:copyright: (c) 2015 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


class BaseModelException(Exception):
    """Model-related exceptions inherit from this base class."""


class ModelConflictException(BaseModelException):
    """A model instance is conflicting with another model instance."""
