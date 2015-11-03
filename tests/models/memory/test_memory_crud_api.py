import pytest
import json

from hypr.models import MemoryModel
from hypr.providers import CRUDProvider


class Model(MemoryModel):

    __key__ = 'id'

    def __init__(self, id, name):
        super().__init__(id=id, name=name)


class Provider(CRUDProvider):

    __model__ = Model


model_under_test = Model


@pytest.mark.usefixtures('filled_db')
class TestMemoryCrudAPI:

    # only a few tests are performed to ensure normal behaviour
    # see model's API tests for an exhaustive collection of tests on the model
    # features
    # see provider's tests for an exhaustive collection of tests on the
    # provider features

    providers = {
        Provider: ('/test', '/test/<int:id>'),
    }

    def test_get_collection(self, app):

        with app.test_client() as client:
            resp = client.get('/test')
            vtt = json.loads(resp.text)

            assert resp.status == 200
            assert vtt['count'] == 1000
            assert len(vtt['result']) == 10

    def test_get_collection_subset(self, app):

        with app.test_client() as client:
            resp = client.get('/test?_limit=5')
            vtt = json.loads(resp.text)

            assert resp.status == 200
            assert vtt['count'] == 1000
            assert len(vtt['result']) == 5

    def test_get_collection_maxset(self, app):

        with app.test_client() as client:
            resp = client.get('/test?_limit=1000')
            vtt = json.loads(resp.text)

            assert resp.status == 200
            assert vtt['count'] == 1000
            assert len(vtt['result']) == 100

    def test_get_existing_resource(self, app):

        with app.test_client() as client:
            resp = client.get('/test/1')

            assert resp.status == 200
            assert json.loads(resp.text) == {'id': 1, 'name': 'user0'}

    def test_get_missing_resource(self, app):

        with app.test_client() as client:
            resp = client.get('/test/0')

            assert resp.status == 404

    def test_get_not_searchable(self, app):

        with app.test_client() as client:
            resp = client.get('/test?_search=user488')

            assert resp.status == 400

    def test_post_new_resource(self, app):

        with app.test_client() as client:
            payload = json.dumps({'id': 1001, 'name': 'test'})
            resp = client.post('/test', data=payload)
            vtt = json.loads(resp.text)

            assert resp.status == 201
            assert  vtt['name'] == 'test'

            resp = client.get('/test/{}'.format(vtt['id']))

            assert resp.status == 200

    def test_post_invalid_resource(self, app):

        with app.test_client() as client:
            payload = json.dumps({'id': 1002, 'unknown': 'test'})
            resp = client.post('/test', data=payload)

            assert resp.status == 400

    def test_post_conflicting_resource(self, app):

        with app.test_client() as client:
            payload = json.dumps({'id': 1, 'name': 'fail'})
            resp = client.post('/test', data=payload)

            assert resp.status == 409

    def test_put_updated_resource(self, app):

        with app.test_client() as client:
            payload = json.dumps({'name': 'success'})
            resp = client.put('/test/1', data=payload)

            assert resp.status == 200
            assert json.loads(resp.text)['name'] == 'success'


    def test_put_conflicting_resource(self, app):

        with app.test_client() as client:
            payload = json.dumps({'id': 2, 'name': 'success'})
            resp = client.put('/test/1', data=payload)

            assert resp.status == 409


    def test_delete_existing_resource(self, app):

        with app.test_client() as client:
            resp = client.delete('/test/50')
            assert resp.status == 204
            resp = client.get('/test/50')
            assert resp.status == 404
