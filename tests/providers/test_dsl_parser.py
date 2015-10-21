import pytest
from hypr.providers.crud import mini_dsl


def test_default_values():

    search, order, limit, offset, filters = mini_dsl({})

    assert search == ()
    assert order == ()
    assert limit == 0
    assert offset == 0
    assert filters == {}


def test_search():

    search, _, _, _, _ = mini_dsl({'_search': ',arg0,arg1,'})
    assert 'arg0' in search
    assert 'arg1' in search


def test_order():

    _, order, _, _, _ = mini_dsl({'_order': 'arg0,arg1'})
    assert 'arg0' in order
    assert 'arg1' in order


def test_limit():

    _, _, limit, _, _ = mini_dsl({'_limit': '2'})
    assert limit == 2


def test_limit_error():

    with pytest.raises(ValueError):
        mini_dsl({'_limit': 'error'})


def test_offset():

    _, _, _, offset, _ = mini_dsl({'_offset': '2'})
    assert offset == 2


def test_offset_error():

    with pytest.raises(ValueError):
        mini_dsl({'_offset': 'error'})


def test_filters():

    _, _, _, _, filters = mini_dsl({'filter0': 'value0', 'filter1': '1,2', 'filter2' : ''})

    assert filters['filter0'] == ('value0',)
    assert '1' in filters['filter1']
    assert '2' in filters['filter1']
    assert filters['filter2'] == ()

