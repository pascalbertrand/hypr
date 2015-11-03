"""
All fixtures common to all models
"""
import pytest

from hypr import Hypr


@pytest.fixture(scope='class')
def init_db(app):
    pass


@pytest.fixture(scope='class')
def empty_db(request, init_db):
    pass


@pytest.fixture(scope='class')
def filled_db(request, init_db):

    Model = request.module.model_under_test

    for i in range(1000):
        user = Model(name='user{}'.format(i))
        user.save(commit=False)
    Model.commit()


@pytest.fixture
def make_model_searchable(request):

    model = request.module.model_under_test
    model.__search__ = 'name'

    def finalizer():
        delattr(model, '__search__')

    request.addfinalizer(finalizer)


@pytest.fixture
def make_model_filtered(request):

    model = request.module.model_under_test
    model.__filters__ = 'name'

    def finalizer():
        delattr(model, '__filters__')

    request.addfinalizer(finalizer)
