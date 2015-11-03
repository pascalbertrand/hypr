import pytest


@pytest.fixture(scope='class')
def init_db(request, app):

    Model = request.module.model_under_test
    Model.reset()

    def finalizer():
        Model.reset()

    request.addfinalizer(finalizer)


@pytest.fixture(scope='class')
def filled_db(request, init_db):

    Model = request.module.model_under_test

    for i in range(1000):
        user = Model(id=i+1, name='user{}'.format(i))
        user.save(commit=False)
    Model.commit()

