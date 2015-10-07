from hypr import Provider
from test_tools import cp_provider_factory


BaseProvider = cp_provider_factory(scope=Provider.PATH)


class Root(Provider):

    propagation_rules = {
        'propagate': 'Resource',
    }


class Resource(BaseProvider):
    
    pass


class TestCPPathScope:

    providers = {
        Root: '/root',
        Resource: '/<int:value>'
    }


    def test_not_path_accept0(self, app):

        with app.test_client() as client:
            vtt = client.get('/0')
            assert vtt.status == 200


    def test_not_path_accept1(self, app):

        with app.test_client() as client:
            vtt = client.get('/1')
            assert vtt.status == 200


    def test_path_accept0(self, app):

        with app.test_client() as client:
            vtt = client.get('/root/0')
            assert vtt.status == 200


    def test_path_reject0(self, app):

        with app.test_client() as client:
            vtt = client.get('/root/1')
            assert vtt.status == 403
