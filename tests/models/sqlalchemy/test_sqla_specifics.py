import pytest

from hypr.models import SqlAlchemyModel, register_engine
from sqlalchemy import Column, Integer, String


@register_engine('sqlite:///:memory:')
class Model(SqlAlchemyModel):

    __tablename__ = 'test_sqla_engine'

    __key__ = 'id', 'name'

    id = Column(Integer, primary_key=True)
    name = Column(String)


model_under_test = Model


@pytest.fixture(scope='class')
def init_db(request, app):

    Model.metadata.create_all()

    def finalizer():
        Model.metadata.drop_all()

    request.addfinalizer(finalizer)


@pytest.mark.usefixtures('empty_db')
class TestSQLAlchemySpecifics:

    def test_model_invalid_key(self, session):

        with pytest.raises(ValueError):
            Model.one(1, _session=session)

    def test_model_valid_key(self, session):

        vtt = Model.one(1, 'User0', _session=session)
        assert vtt is None
