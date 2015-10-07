import json
from hypr import Provider


class MyProvider(Provider):

    def get(self, value=None):
        if value is None:
            return 'ok'
        return value

    def post(self, **kwargs):
        return kwargs



class TestProvider:

    providers = {
        MyProvider: ('/', '/<int:value>', '/<string:another>/<int:value>')
    }

    def test_request_0(self, app):

        with app.test_client() as client:

            resp = client.get('/')

            assert resp.status == 200
            assert json.loads(resp.text) == 'ok'


    def test_request_1(self, app):

        with app.test_client() as client:

            resp = client.get('/1')

            assert resp.status == 200
            assert json.loads(resp.text) == 1


    def test_request_2(self, app):

        with app.test_client() as client:

            resp = client.get('/foo/1')

            assert resp.status == 200
            assert json.loads(resp.text) == 1


    def test_request_3(self, app):

        with app.test_client() as client:

            resp = client.post('/1')

            assert resp.status == 200
            assert json.loads(resp.text) == {'value': 1}


    def test_request_4(self, app):

        with app.test_client() as client:

            resp = client.post('/foo/1')

            assert resp.status == 200
            assert json.loads(resp.text) == {'another': 'foo', 'value': 1}

