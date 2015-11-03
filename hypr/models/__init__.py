"""
hypr.models
-----------

:copyright: (c) 2015 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


from hypr.models.memory import MemoryModel

try:
    from hypr.models.sqlalchemy import SqlAlchemyModel, register_engine
except ImportError:
    pass

# Automatically generate the list of availables models

__all__ = [name for name in locals().keys() if not name.endswith('Model')]
