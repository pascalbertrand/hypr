from hypr import Provider, filter
import json


class Root(Provider):

    propagation_rules = {
        'propagate': 'Resource',
    }

    @filter
    def default_filter(self, value):
        return value


class TestDefaultFilter:

    providers = {
        'Root': '/root/<int:value>',
        'Resource': '/resource'
    }

    def test_static_method_filter(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/resource')
            assert resp.status == 200
            assert json.loads(resp.text) == {'Root': 1}
