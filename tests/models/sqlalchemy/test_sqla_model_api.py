import pytest

from sqlalchemy import Column, Integer, String

from hypr.models import SqlAlchemyModel
from hypr.exc import ModelSearchException, ModelFilterException, \
    ModelConflictException


class User(SqlAlchemyModel):

    __tablename__ = 'test_sqla_model_api'

    id = Column(Integer, primary_key=True)
    name = Column(String)


model_under_test = User


@pytest.mark.usefixtures('empty_db')
class TestSQLAlchemyModelAPI_0:
    # All those tests are ran against an empty db

    def test_session_required(self):
        """
        Outside of the context of a coroutine a RuntimeError is raised if the
        session is not explicitly passed.
        """

        with pytest.raises(RuntimeError) as exc:
            user = User(name='test')
            user.save()

    def test_one_not_found(self, session):

        vtt = User.one(1, _session=session)

        assert vtt is None

    def test_get_empty(self, session):

        vtt = User.get(_session=session)

        assert vtt == []

    def test_create_instance(self, session):

        user = User(name='test')
        user.save(_session=session)
        vtt = User.one(user.id, _session=session)

        assert vtt
        assert vtt.name == 'test'


@pytest.mark.usefixtures('filled_db')
class TestSQLAlchemyModelAPI_1:
    # All those tests are ran against a db filled with 1000 records.

    def test_one(self, session):

        vtt = User.one(1, _session=session)

        assert vtt.id == 1
        assert vtt.name == 'user0'

    def test_get_default_limit(self, session):

        vtt = User.get(_session=session)

        assert len(vtt) == 10

    def test_get_custom_limit(self, session):

        vtt = User.get(_limit=5, _session=session)

        assert len(vtt) == 5

    def test_get_absolute_limit(self, session):

        vtt = User.get(_limit=1000, _session=session)

        assert len(vtt) == 100

    def test_get_offset(self, session):

        vtt0 = User.get(_limit=10, _session=session)
        vtt1 = User.get(_limit=10, _offset=1, _session=session)

        assert len(vtt0) == 10
        assert len(vtt1) == 10
        assert vtt0[0] not in vtt1
        assert vtt1[-1] not in vtt0
        assert vtt0[1] == vtt1[0]

    def test_get_order(self, session):

        vtt0 = User.get(_order='!name', _limit=10, _session=session)
        vtt1 = User.get(_order='name', _limit=10, _session=session)

        for i in range(9):
            assert vtt0[i].name > vtt0[i+1].name

        for i in range(9):
            assert vtt1[i].name < vtt1[i+1].name

        for obj in vtt0:
            assert obj not in vtt1

    def test_count(self, session):

        vtt = User.count(_session=session)

        assert vtt == 1000

    def test_get_not_searchable(self, session):

        with pytest.raises(ModelSearchException):
            User.get(_search='anything', _session=session)

    def test_get_filter_one_term(self, session):

        vtt = User.get(name='user17', _session=session)

        assert len(vtt) == 1
        assert vtt[0].name == 'user17'
        assert vtt[0].id == 18

    def test_get_filter_multiple_terms(self, session):

        vtt = User.get(name=('user17', 'user483'), _session=session)

        assert len(vtt) == 2
        assert 'user17' in (obj.name for obj in vtt)
        assert 'user483' in (obj.name for obj in vtt)

    def test_get_multiple_filters(self, session):

        vtt = User.get(name=('user17', 'user483'), id=18, _session=session)

        assert len(vtt) == 1
        assert vtt[0].name == 'user17'

    @pytest.mark.usefixtures('make_model_filtered')
    def test_get_explicit_filters(self, session):

        with pytest.raises(ModelFilterException) as exc:
          User.get(name=('user17', 'user483'), id=18, _session=session)

        assert '`id`' in str(exc)

    @pytest.mark.usefixtures('make_model_searchable')
    def test_get_search_one_term(self, session):

        vtt = User.get(_search='user555', _session=session)

        assert len(vtt) == 1

    @pytest.mark.usefixtures('make_model_searchable')
    def test_get_search_multiple_term(self, session):

        vtt = User.get(_search=('user555', 'user443'), _session=session)

        assert len(vtt) == 2

    def test_delete_autocommit(self, session):

        target = User.one(10, _session=session)
        target.delete(_session=session)

        assert User.one(10, _session=session) is None

    def test_delete_manual_commit(self, session):

        target = User.one(11, _session=session)
        target.delete(commit=False, _session=session)
        User.commit(_session=session)

        assert User.one(11, _session=session) is None

    def test_delete_rollback(self, session):

        target = User.one(12, _session=session)
        target.delete(commit=False, _session=session)
        User.rollback(_session=session)

        assert User.one(12, _session=session) is target

    def test_save_autocommit(self, session):

        target = User.one(1, _session=session)
        target.name = 'modified'
        target.save(_session=session)
        vtt = User.one(1, _session=session)

        assert vtt.name == 'modified'

    def test_save_manual_commit(self, session):

        target = User.one(1, _session=session)
        target.name = 'modified'
        target.save(commit=False, _session=session)
        User.commit(_session=session)
        vtt = User.one(1, _session=session)

        assert vtt.name == 'modified'

    def test_save_rollback(self, session):

        target = User.one(2, _session=session)
        target.name = 'modified'
        target.save(commit=False, _session=session)
        User.rollback(_session=session)

        vtt = User.one(2, _session=session)
        assert vtt.name == 'user1'

    def test_conflict(self, session):

        with pytest.raises(ModelConflictException):
            target = User.one(1, _session=session)
            target.id = 3
            target.save(_session=session)
