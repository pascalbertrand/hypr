from hypr import Provider
from test_tools import cp_provider_factory


BaseProvider = cp_provider_factory(scope=('propagate', 'alternate'))


class Root(BaseProvider):

    propagation_rules = {
        'propagate': 'Resource',
        'alternate': ('Resource', '/alt')
    }


class Resource(Provider):

    def get(self):
        return 'ok'

class TestCPMultiScope:

    providers = {
        'Root': '/<int:value>',
        'Resource': '/res'
    }

    def test_direct_accept0(self, app):

        with app.test_client() as client:
            vtt = client.get('/0')
            assert vtt.status == 200


    def test_direct_accept1(self, app):

        with app.test_client() as client:
            vtt = client.get('/1')
            assert vtt.status == 200


    def test_indirect_accept0(self, app):

        with app.test_client() as client:
            vtt = client.get('/0/res')
            assert vtt.status == 200


    def test_indirect_accept1(self, app):

        with app.test_client() as client:
            vtt = client.get('/0/alt')
            assert vtt.status == 200


    def test_indirect_accept2(self, app):

        with app.test_client() as client:
            vtt = client.get('/1/alt')
            assert vtt.status == 403

    def test_indirect_reject(self, app):

        with app.test_client() as client:
            vtt = client.get('/1/res')
            assert vtt.status == 403
