from hypr import Provider
from test_tools import cp_provider_factory


BaseProvider = cp_provider_factory(scope=Provider.ENTRY)


class Root(Provider):

    propagation_rules = {
        'propagate': 'Resource',
    }


class Resource(BaseProvider):
    
    pass


class TestCPEntryScope:

    providers = {
        Root: '/root', 
        Resource: '/<int:value>',
    }


    def test_entry_accept(self, app):

        with app.test_client() as client:
            vtt = client.get('/0')
            assert vtt.status == 200

    def test_entry_abort(self, app):

        with app.test_client() as client:
            vtt = client.get('/1')
            assert vtt.status == 403

    def test_not_entry(self, app):

        with app.test_client() as client:
            vtt = client.get('/root/1')
            assert vtt.status == 200
