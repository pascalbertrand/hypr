import pytest
import json
from hypr.models import MemoryModel
from hypr.providers import CRUDProvider


class MyModel(MemoryModel):

    __key__ = 'id'


@pytest.fixture
def init_data(request):

    MyModel(id=0, value='ok')
    MyModel(id=1, value='ok')
    MyModel.commit()

    def finalizer():
        MyModel.reset()

    request.addfinalizer(finalizer)


class MyProvider(CRUDProvider):

    __model__ = MyModel


@pytest.mark.usefixtures('init_data')
class TestDebug:

    providers = {
        MyProvider: ('/test', '/test/<int:id>'),
    }

    def test_get_collection(self, app):

        with app.test_client() as client:
            resp = client.get('/test')
            assert resp.status == 200
            assert json.loads(resp.text) == {'count': 2, 'result': [{'id': 0, 'value': 'ok'}, {'id': 1, 'value': 'ok'}]}

    def test_get_part_collection(self, app):

        with app.test_client() as client:
            resp = client.get('/test?_limit=1')
            assert resp.status == 200
            assert json.loads(resp.text) == {'count': 2, 'result': [{'id': 0, 'value': 'ok'}]}

    def test_get_existing_resource(self, app):

        with app.test_client() as client:
            resp = client.get('/test/0')
            assert resp.status == 200
            assert json.loads(resp.text) == {'id': 0, 'value': 'ok'}

    def test_get_missing_resource(self, app):

        with app.test_client() as client:
            resp = client.get('/test/2')
            assert resp.status == 404

    def test_incomplete_post(self, app):

        with app.test_client() as client:
            resp = client.post('/test')
            assert resp.status == 400

    def test_post_new_resource(self, app):

        with app.test_client() as client:

            payload = json.dumps({'id': 2, 'value': 'test'})
            resp = client.post('/test', data=payload)
            assert resp.status == 201
            assert json.loads(resp.text) == json.loads(payload)

            resp = client.get('/test/2')
            assert resp.status == 200

    def test_post_conflicting_resource(self, app):

        with app.test_client() as client:

            payload = json.dumps({'id': 1, 'value': 'test'})
            resp = client.post('/test', data=payload)
            assert resp.status == 409

    def test_invalid_put(self, app):

        with app.test_client() as client:

            payload = json.dumps({'id': 1, 'value': 'test'})
            resp = client.put('/test', data=payload)
            assert resp.status == 400

    def test_put_updated_resource(self, app):

        with app.test_client() as client:

            payload = json.dumps({'id': 1, 'value': 'test'})
            resp = client.put('/test/1', data=payload)
            assert resp.status == 200
            assert json.loads(resp.text) == json.loads(payload)

    def test_put_updated_resource_pk_error(self, app):

        with app.test_client() as client:

            payload = json.dumps({'id': 2, 'value': 'test'})
            resp = client.put('/test/1', data=payload)
            assert resp.status == 409

    def test_delete_existing_resource(self, app):

        with app.test_client() as client:

            resp = client.delete('/test/1')
            assert resp.status == 204

            resp = client.get('/test/1')
            assert resp.status == 404

    def test_delete_inexisting_resource(self, app):

        with app.test_client() as client:

            resp = client.delete('/test/6')
            assert resp.status == 404
