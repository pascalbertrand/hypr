from hypr import Hypr, Provider, Response, checkpoint, abort
from hypr import Provider
from test_tools import cp_provider_factory


BaseProvider = cp_provider_factory(scope=Provider.TRANSFER)


class Root(BaseProvider):

    propagation_rules = {
        'propagate': 'Resource',
        'alternate': ('Resource', '/alternate')
    }


class TestCPEntryScope:

    providers = {
        'Root': '/<int:value>',
        'Resource': '/resource'
    }

    def test_no_transfer_accept(self, app):

        with app.test_client() as client:
            vtt = client.get('/1')
            assert vtt.status == 200

    def test_transfer_reject(self, app):

        with app.test_client() as client:
            vtt = client.get('/1/resource')
            assert vtt.status == 403

    def test_transfer_accept(self, app):

        with app.test_client() as client:
            vtt = client.get('/0/resource')
            assert vtt.status == 200


    def test_transfer_alt_reject(self, app):

        with app.test_client() as client:
            vtt = client.get('/1/alternate')
            assert vtt.status == 403

    def test_transfer_alt_accept(self, app):

        with app.test_client() as client:
            vtt = client.get('/0/alternate')
            assert vtt.status == 200

