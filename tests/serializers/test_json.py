import pytest
from hypr.serializers import json_serializer
from datetime import datetime, date


def test_datetime():

    dt = datetime.now()
    assert json_serializer(dt) == '"{}"'.format(dt.isoformat())


def test_date():

    dt = date.today()
    assert json_serializer(dt) == '"{}T00:00:00"'.format(dt.isoformat())


def test_serializable_object():

    class Serializable():

        def __serialize__(self):
            return 'ok'

    assert json_serializer(Serializable()) == '"ok"'


def test_unserializable_object():

    class Unserializable():
        pass

    with pytest.raises(TypeError):
        json_serializer(Unserializable())


