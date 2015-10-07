import pytest
from hypr import Provider
from hypr.provider import filter


class BaseProvider(Provider):

    @filter(requires='value')
    def custom_filter(self, value=None):
        return value

    def get(self, value=None):
        if value is None:
            return 'ok'
        return value


class Root(BaseProvider):

    propagation_rules = {
        'next': 'Node',
        'alternate': ('Node', '/altnode', '/altnode/<int:value>'),
    }


class Node(BaseProvider):

    propagation_rules = {
        'next': 'Resource',
    }


class TestPropagationRequirements:

    providers = {
        'Root': ('/root', '/root/<int:value>'),
        'Node': ('/node', '/node/<int:value>'),
        'Resource': '/resource'
    }

    def test_simple_propagation(self, app):

        with app.test_client() as client:

            resp = client.get('/root')
            assert resp.status == 200

            resp = client.get('/root/1')
            assert resp.status == 200

            resp = client.get('/root/node')
            assert resp.status == 404

            resp = client.get('/root/1/node')
            assert resp.status == 200

    def test_two_hops_propagation(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/node/resource')
            assert resp.status == 404

            resp = client.get('/root/1/node/1/resource')
            assert resp.status == 200

    def test_alternate_propagation(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/altnode/resource')
            assert resp.status == 404

            resp = client.get('/root/1/altnode/1/resource')
            assert resp.status == 200

