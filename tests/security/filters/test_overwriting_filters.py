from test_tools import fltr_provider_factory
import json


FilterProvider = fltr_provider_factory(key='my_filter')


class Root(FilterProvider):

    propagation_rules = {
        'propagate': 'Node',
    }


class Node(FilterProvider):

    propagation_rules = {
        'propagate': 'Resource',
    }


class TestOverwritingFilter:

    providers = {
        Root: '/root/<int:value>',
        Node: '/node/<int:value>',
        'Resource': '/resource',
    }

    def test_propagate_0(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/node/2')
            assert resp.status == 200
            assert json.loads(resp.text) == {'my_filter': 1}

    def test_propagate_1(self, app):

        with app.test_client() as client:

            resp = client.get('/node/2/resource')
            assert resp.status == 200
            assert json.loads(resp.text) == {'my_filter': 2}

    def test_propagate_2(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/node/2/resource')
            assert resp.status == 200
            assert json.loads(resp.text) == {'my_filter': 2}
