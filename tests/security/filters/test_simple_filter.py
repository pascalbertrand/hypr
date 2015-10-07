from test_tools import fltr_provider_factory
import json


FilterProvider = fltr_provider_factory()


class Root(FilterProvider):

    propagation_rules = {
        'propagate': 'Resource',
    }


class TestSimpleFilter:

    providers = {
        'Root': '/root/<int:value>',
        'Resource': '/resource'
    }

    def test_static_method_filter(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/resource')
            assert resp.status == 200
            assert json.loads(resp.text) == {'Root': 1}
