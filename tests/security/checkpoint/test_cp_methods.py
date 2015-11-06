import pytest

import json
from hypr import Hypr, Provider, checkpoint, abort


class MyProvider(Provider):

    value = 0

    @checkpoint(priority=0)
    def reset_values(self):
        self.all = False
        self.get_only = False
        self.get_and_post = False

    @checkpoint
    def all_methods(self):
        self.all = True

    @checkpoint(methods='GET')
    def get_only_method(self):
        self.get_only = True

    @checkpoint(methods=('GET', 'POST'))
    def get_and_post_method(self):
        self.get_and_post = True

    def meth(self):
        return {'all': self.all,
                'get': self.get_only,
                'get_post': self.get_and_post}

    def get(self):
        return self.meth()

    def post(self):
        return self.meth()

    def delete(self):
        return self.meth()

@pytest.fixture(scope='class')
def app():

    app = Hypr()
    app.router.add_provider(MyProvider, '/test')
    return app


class TestCheckpointMethods:

    def test_get(self, app):

        with app.test_client() as client:

            resp = client.get('/test')
            vtt = json.loads(resp.text)

            assert vtt['all']
            assert vtt['get']
            assert vtt['get_post']

    def test_post(self, app):

        with app.test_client() as client:

            resp = client.post('/test')
            vtt = json.loads(resp.text)

            assert vtt['all']
            assert not vtt['get']
            assert vtt['get_post']

    def test_delete(self, app):

        with app.test_client() as client:

            resp = client.delete('/test')
            vtt = json.loads(resp.text)

            assert vtt['all']
            assert not vtt['get']
            assert not vtt['get_post']

