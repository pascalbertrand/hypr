"""
hypr.config
-----------

:copyright: (c) 2014 by Morgan Delahaye-Prat.
:license: BSD, see LICENSE for more details.
"""


import os
import types


class Config(dict):

    def __init__(self, root_path=None, defaults=None):
        dict.__init__(self, defaults or {})
        self.root_path = root_path or '.'

    def from_envvar(self, variable_name, silent=False):
        """
        Loads a configuration from an environment variable pointing to a
        configuration file.
        """

        err_msg = ('The environment variable {} is not set and as such '
                   'configuration could not be loaded. Set this variable and '
                   'make it point to a configuration file')

        rv = os.environ.get(variable_name)
        if not rv:
            if silent:
                return False
            raise RuntimeError(err_msg.format(variable_name))
        return self.from_pyfile(rv, silent=silent)

    def from_pyfile(self, filename, silent=False):
        """
        """

        err_msg = 'Unable to load configuration file ({})'

        filename = os.path.join(self.root_path, filename)
        d = types.ModuleType('config')
        d.__file__ = filename
        try:
            with open(filename) as config_file:
                exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
        except IOError as e:
            if silent:
                return False
            e.strerror = err_msg.format(e.strerror)
            raise
        self.from_object(d)

    def from_object(self, obj):

        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def get_namespace(self, namespace, lowercase=True, trim_namespace=True):
        """Returns a dictionary containing a subset of configuration options
        that match the specified namespace/prefix. Example usage::
            app.config['IMAGE_STORE_TYPE'] = 'fs'
            app.config['IMAGE_STORE_PATH'] = '/var/app/images'
            app.config['IMAGE_STORE_BASE_URL'] = 'http://img.website.com'
            image_store_config = app.config.get_namespace('IMAGE_STORE_')
        The resulting dictionary `image_store` would look like::
            {
                'type': 'fs',
                'path': '/var/app/images',
                'base_url': 'http://img.website.com'
            }
        This is often useful when configuration options map directly to
        keyword arguments in functions or class constructors.
        :param namespace: a configuration namespace
        :param lowercase: a flag indicating if the keys of the resulting
                          dictionary should be lowercase
        :param trim_namespace: a flag indicating if the keys of the resulting
                          dictionary should not include the namespace
        """
        rv = {}
        for k, v in self.items():
            if not k.startswith(namespace):
                continue
            if trim_namespace:
                key = k[len(namespace):]
            else:
                key = k
            if lowercase:
                key = key.lower()
            rv[key] = v
        return rv
