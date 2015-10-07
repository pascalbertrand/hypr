import json
import pytest
from test_tools import ProviderTemplate
from hypr import Hypr, Provider


class CustomProvider(Provider):

    def get(self):
        return 'get'

    def post(self):
        return 'post'

    def put(self):
        return 'put'

    def delete(self):
        return 'delete'


class TestBasicRouting:

    providers = {
        'Resource0': '/res0',
        'Resource1': '/res1',
        'Resource2': '/res2/',
    }

    def test_res0(self, app):

        with app.test_client() as client:

            resp = client.get('/res0')
            assert resp.status == 200
            assert json.loads(resp.text) == {'Resource0': 'ok'}

    def test_res1(self, app):

        with app.test_client() as client:

            resp = client.get('/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == {'Resource1': 'ok'}

    def test_res2_wo_slash(self, app):

        with app.test_client() as client:

            resp = client.get('/res2')
            assert resp.status == 200
            assert json.loads(resp.text) == {'Resource2': 'ok'}

    def test_res2_w_shash(self, app):

        with app.test_client() as client:

            resp = client.get('/res2/')
            assert resp.status == 200
            assert json.loads(resp.text) == {'Resource2': 'ok'}

    def test_res3(self, app):

        with app.test_client() as client:

            resp = client.get('/res3')
            assert resp.status == 404


class TestVerb:

    providers = {
        'Resource0': '/res0',
        'CustomProvider': '/res1',
    }

    def test_get_res0(self, app):

        with app.test_client() as client:
            resp = client.get('/res0')
            assert resp.status == 200
            assert json.loads(resp.text) == {'Resource0': 'ok'}


    def test_get_res1(self, app):

        with app.test_client() as client:
            resp = client.get('/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'get'

    def test_post_res0(self, app):

        with app.test_client() as client:
            resp = client.post('/res0')
            assert resp.status == 405

    def test_post_res1(self, app):

        with app.test_client() as client:
            resp = client.post('/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'post'

    def test_put_res0(self, app):

        with app.test_client() as client:
            resp = client.put('/res0')
            assert resp.status == 405

    def test_put_res1(self, app):

        with app.test_client() as client:
            resp = client.put('/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'put'

    def test_delete_res0(self, app):

        with app.test_client() as client:
            resp = client.delete('/res0')
            assert resp.status == 405

    def test_delete_res1(self, app):

        with app.test_client() as client:
            resp = client.delete('/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'delete'


class TestPropagationAndVerbs:

    prop_0 = type('prop_0', (ProviderTemplate,), {})
    prop_1 = type('prop_1', (CustomProvider,), {})
    prop_2 = type('prop_2', (ProviderTemplate,), {})

    prop_0.propagation_rules = {'next': prop_1, 'next2': prop_2}
    prop_1.propagation_rules = {'next': prop_0}
    prop_2.propagation_rules = {'next': prop_0}
    
    providers = {
        prop_0: '/res0',
        prop_1: '/res1',
        prop_2: '/res2/',
    }

    def test_get_res0(self, app):

        with app.test_client() as client:
            resp = client.get('/res1/res0')
            assert resp.status == 200
            assert json.loads(resp.text) == {'prop_0': 'ok'}

    def test_get_res1(self, app):

        with app.test_client() as client:
            resp = client.get('/res0/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'get'

    def test_get_res2_res0(self, app):

        with app.test_client() as client:
            resp = client.get('/res2/res0')
            assert resp.status == 200
            assert json.loads(resp.text) == {'prop_0': 'ok'}

    def test_get_res0_res2_wo_slashes(self, app):

        with app.test_client() as client:
            resp = client.get('/res0/res2')
            assert resp.status == 200
            assert json.loads(resp.text) == {'prop_2': 'ok'}

    #def test_get_res0_res2_w_slash(self, app):

    #    with app.test_client() as client:
    #        resp = client.get('/res0/res2/')
    #        assert resp.status == 200
    #        assert json.loads(resp.text) == {'prop_2': 'ok'}

    def test_post_res0(self, app):

        with app.test_client() as client:
            resp = client.post('/res1/res0')
            assert resp.status == 405

    def test_post_res1(self, app):

        with app.test_client() as client:
            resp = client.post('/res0/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'post'

    def test_put_res0(self, app):

        with app.test_client() as client:
            resp = client.put('/res1/res0')
            assert resp.status == 405

    def test_put_res1(self, app):

        with app.test_client() as client:
            resp = client.put('/res0/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'put'

    def test_delete_res0(self, app):

        with app.test_client() as client:
            resp = client.delete('/res1/res0')
            assert resp.status == 405

    def test_delete_res1(self, app):

        with app.test_client() as client:
            resp = client.delete('/res0/res1')
            assert resp.status == 200
            assert json.loads(resp.text) == 'delete'


class TestPropagation:

    my_provider = type('MyProvider', (ProviderTemplate,), {})

    providers = {
        my_provider: '/test'
    }

    def test_no_propagation_route(self, app):

        self.my_provider.propagation_rules = {'next': Provider}
        with pytest.raises(AssertionError) as err:
            app.propagate()

        assert 'No URLs available to reach \'Provider\'' in str(err)

    def test_propagation_route(self, app):

        self.my_provider.propagation_rules = {'next': (ProviderTemplate, '/next')}
        app.propagate()

        with app.test_client() as client:

            resp = client.get('/test/next')
            assert resp.status == 200


class TestRuleErrors:

    def test_duplicate_variable_name(self, app):
        
        with pytest.raises(ValueError) as err:
            app.router.add_provider(Provider, '/<int:value>/<int:value>')

        assert 'variable name \'value\' used twice.' in str(err)

    def test_malformed_rule(self, app):
        
        with pytest.raises(ValueError) as err:
            app.router.add_provider(Provider, '/<int:value')

        assert 'malformed url rule' in str(err)

    def test_leading_slash_required(self, app):
        
        with pytest.raises(ValueError) as err:
            app.router.add_provider(Provider, 'foo/bar')

        assert 'URL should be started with \'/\'' in str(err)
