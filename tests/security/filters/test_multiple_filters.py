import pytest, json
from hypr import Hypr, Provider, request
from hypr.provider import filter


class Root(Provider):

    propagation_rules = {
        'propagate': 'Resource',
    }

    @filter(key='Root0')
    def mandatory_filter0(self, value):
        return value

    @filter(key='Root1')
    def mandatory_filter1(self, value):
        return value

    def get(self, value):
        return 'ok'

    
class Resource(Provider):

    def get(self, value=None):
        return request.m_filters


@pytest.fixture(scope='module')
def app():

    app = Hypr()
    app.router.add_provider(Root, '/root/<int:value>')
    app.router.add_provider(Resource, '/resource')
    app.propagate()

    return app


def test_sanity_check(app):

    with app.test_client() as client:
        vtt = client.get('/root/1')
        assert vtt.status == 200

        vtt = client.get('/resource')
        assert vtt.status == 200


def test_propagate(app):

    with app.test_client() as client:

        resp = client.get('/root/1/resource')
        vtt = json.loads(resp.text)        

        assert resp.status == 200
        assert vtt['Root0'] == 1
        assert vtt['Root1'] == 1

