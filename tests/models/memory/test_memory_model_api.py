import pytest


from hypr.models import MemoryModel
from hypr.providers import CRUDProvider
from hypr.exc import ModelSearchException, ModelFilterException, \
    ModelConflictException


class Model(MemoryModel):

    __key__ = 'id'

    def __init__(self, id, name):
        super().__init__(id=id, name=name)


model_under_test = Model


@pytest.mark.usefixtures('empty_db')
class TestMemoryModelAPI_0:
    # All those tests are ran against an empty db


    def test_one_not_found(self):

        vtt = Model.one(1)
        assert vtt is None

    def test_get_empty(self):

        vtt = Model.get()
        assert vtt == []

    def test_create_instance(self):

        model = Model(id=1, name='test')
        model.save()
        vtt = Model.one(model.id)

        assert vtt
        assert vtt.name == 'test'


@pytest.mark.usefixtures('filled_db')
class TestMemoryModelAPI_1:
    # All those tests are ran against a db filled with 1000 records.

    def test_one(self):

        vtt = Model.one(1)

        assert vtt.id == 1
        assert vtt.name == 'user0'

    def test_get_default_limit(self):

        vtt = Model.get()

        assert len(vtt) == 10

    def test_get_custom_limit(self):

        vtt = Model.get(_limit=5)

        assert len(vtt) == 5

    def test_get_absolute_limit(self):

        vtt = Model.get(_limit=1000)

        assert len(vtt) == 100

    def test_get_offset(self):

        vtt0 = Model.get(_limit=10)
        vtt1 = Model.get(_limit=10, _offset=1)

        assert len(vtt0) == 10
        assert len(vtt1) == 10
        assert vtt0 != vtt1

    def test_count(self):

        vtt = Model.count()

        assert vtt == 1000

    def test_get_not_searchable(self):

        with pytest.raises(ModelSearchException):
            Model.get(_search='anything')

    def test_get_filter_one_term(self):

        vtt = Model.get(name='user17')

        assert len(vtt) == 1
        assert vtt[0].name == 'user17'
        assert vtt[0].id == 18

    def test_get_filter_multiple_terms(self):

        vtt = Model.get(name=('user17', 'user483'))

        assert len(vtt) == 2
        assert 'user17' in (obj.name for obj in vtt)
        assert 'user483' in (obj.name for obj in vtt)

    def test_get_multiple_filters(self):

        vtt = Model.get(name=('user17', 'user483'), id=18)

        assert len(vtt) == 1
        assert vtt[0].name == 'user17'

    @pytest.mark.usefixtures('make_model_filtered')
    def test_get_explicit_filters(self):

        with pytest.raises(ModelFilterException) as exc:
            Model.get(name=('user17', 'user483'), id=18)

        assert '`id`' in str(exc)

    @pytest.mark.usefixtures('make_model_searchable')
    def test_get_search_always_fail(self):

        with pytest.raises(ModelSearchException):
            Model.get(_search='user555')

    def test_delete_autocommit(self):

        target = Model.one(10)
        target.delete()

        assert Model.one(10) is None

    def test_delete_manual_commit(self):

        target = Model.one(11)
        target.delete(commit=False)
        Model.commit()

        assert Model.one(11) is None

    def test_delete_rollback(self):

        target = Model.one(12)
        target.delete(commit=False)
        Model.rollback()

        assert Model.one(12)

    def test_save_autocommit(self):

        target = Model.one(1)
        target.name = 'modified'
        target.save()
        vtt = Model.one(1)

        assert vtt.name == 'modified'

    def test_save_manual_commit(self):

        target = Model.one(1)
        target.name = 'modified'
        target.save(commit=False)
        Model.commit()
        vtt = Model.one(1)

        assert vtt.name == 'modified'

    def test_save_rollback(self):

        target = Model.one(2)
        target.name = 'modified'
        target.save(commit=False)
        Model.rollback()

        vtt = Model.one(2)
        assert vtt.name == 'user1'

    def test_conflict(self):

        with pytest.raises(ModelConflictException):
            target = Model.one(1)
            target.id = 3
            target.save()
