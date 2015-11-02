import pytest


@pytest.fixture(scope='class')
def session(request):

    Model = request.module.model_under_test
    return Model.session()


@pytest.fixture(scope='class')
def init_db(request, app):

    Model = request.module.model_under_test

    Model.register_engine()          # Use the default engine
    Model.metadata.create_all()

    def finalizer():
        Model.metadata.drop_all()

    request.addfinalizer(finalizer)


@pytest.fixture(scope='class')
def filled_db(request, init_db, session):

    Model = request.module.model_under_test

    for i in range(1000):
        user = Model(name='user{}'.format(i))
        user.save(commit=False, _session=session)
    Model.commit(_session=session)

