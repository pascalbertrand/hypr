import os
import sys
import pytest

from hypr import Hypr
from hypr.config import Config


# config keys used for the TestConfig
TEST_KEY = 'foo'
SECRET_KEY = 'devkey'


def common_object_test(app):
    assert app.config['TEST_KEY'] == 'foo'
    assert 'TestConfig' not in app.config


def test_config_from_file():
    app = Hypr()
    app.config.from_pyfile(__file__.rsplit('.', 1)[0] + '.py')
    common_object_test(app)


def test_config_from_object():
    app = Hypr()
    app.config.from_object(sys.modules[__name__])
    common_object_test(app)


def test_config_from_class():

    class Base:
        TEST_KEY = 'foo'

    class Test(Base):
        SECRET_KEY = 'devkey'

    app = Hypr()
    app.config.from_object(Test)
    common_object_test(app)


def test_config_from_envvar():

    env = os.environ
    try:
        os.environ = {}
        app = Hypr()
        with pytest.raises(RuntimeError):
            app.config.from_envvar('FOO_SETTINGS')
        app.config.from_envvar('FOO_SETTINGS', silent=True)

        os.environ = {'FOO_SETTINGS': __file__.rsplit('.', 1)[0] + '.py'}
        app.config.from_envvar('FOO_SETTINGS')
        common_object_test(app)
    finally:
        os.environ = env


def test_config_from_envvar_missing():
    env = os.environ
    try:
        app = Hypr()
        os.environ = {'FOO_SETTINGS': 'missing.cfg'}
        with pytest.raises(IOError):    
            app.config.from_envvar('FOO_SETTINGS')

        app.config.from_envvar('FOO_SETTINGS', silent=True)
    finally:
        os.environ = env


def test_config_missing():
    app = Hypr()
    try:
        app.config.from_pyfile('missing.cfg')
    except IOError as e:
        msg = str(e)
        assert msg.startswith('[Errno 2] Unable to load configuration '
                              'file (No such file or directory):')
        assert msg.endswith("missing.cfg'")
    else:
        assert 0, 'expected config'
    assert not app.config.from_pyfile('missing.cfg', silent=True)


def test_custom_config_class():
    class CustomConfig(Config):
        pass

    class MyHypr(Hypr):
        config_class = CustomConfig

    app = MyHypr()
    assert isinstance(app.config, CustomConfig)
    app.config.from_object(sys.modules[__name__])
    common_object_test(app)


def test_get_namespace():
    app = Hypr()
    app.config['FOO_OPTION_1'] = 'foo option 1'
    app.config['FOO_OPTION_2'] = 'foo option 2'
    app.config['BAR_STUFF_1'] = 'bar stuff 1'
    app.config['BAR_STUFF_2'] = 'bar stuff 2'
    foo_options = app.config.get_namespace('FOO_')
    assert 2 == len(foo_options)
    assert 'foo option 1' == foo_options['option_1']
    assert 'foo option 2' == foo_options['option_2']
    bar_options = app.config.get_namespace('BAR_', lowercase=False)
    assert 2 == len(bar_options)
    assert 'bar stuff 1' == bar_options['STUFF_1']
    assert 'bar stuff 2' == bar_options['STUFF_2']
    foo_options = app.config.get_namespace('FOO_', trim_namespace=False)
    assert 2 == len(foo_options)
    assert 'foo option 1' == foo_options['foo_option_1']
    assert 'foo option 2' == foo_options['foo_option_2']
    bar_options = app.config.get_namespace('BAR_', lowercase=False, trim_namespace=False)
    assert 2 == len(bar_options)
    assert 'bar stuff 1' == bar_options['BAR_STUFF_1']
    assert 'bar stuff 2' == bar_options['BAR_STUFF_2']

